import pytest

from jumpup import (
    Bounds,
    ClaimSelectionMode,
    GameAction,
    GameConfig,
    GamePhase,
    GameState,
    House,
    InvalidTransitionError,
    Layout,
    LayoutType,
    Player,
    Point,
    RoundState,
    Stone,
    transition,
)
from jumpup.geometry import HouseGeometry


def make_state(config: GameConfig | None = None) -> GameState:
    geometry = HouseGeometry(
        boundary=(Point(0, 0), Point(10, 0), Point(10, 10), Point(0, 10), Point(0, 0)),
        bounds=Bounds(0, 0, 10, 10),
    )
    layout = Layout(
        id="claims",
        type=LayoutType.HEART,
        houses=tuple(
            House(id=f"h{i}", number=i, sequence_index=i - 1, geometry=geometry)
            for i in range(1, 4)
        ),
    )
    players = (
        Player(id="p1", name="Player 1", stone_id="s1", order=0),
        Player(id="p2", name="Player 2", stone_id="s2", order=1),
    )
    stones = (
        Stone(id="s1", owner_id="p1"),
        Stone(id="s2", owner_id="p2"),
    )
    return GameState.initial(layout, players, stones, config or GameConfig())


def claim_selection_state(config: GameConfig | None = None) -> GameState:
    state = make_state(config)
    state = transition(state, GameAction.start_game()).state
    state = transition(state, GameAction.begin_turn("p1")).state
    state = transition(state, GameAction.throw("h1")).state
    state = transition(state, GameAction.resolve_throw(True)).state
    state = transition(state, GameAction.begin_hopping_out(("h2", "h3"))).state
    state = transition(state, GameAction.hop("h2", Point(5, 5))).state
    state = transition(state, GameAction.hop("h3", Point(5, 5))).state
    state = transition(state, GameAction.begin_hopping_back()).state
    state = transition(state, GameAction.hop("h2", Point(5, 5))).state
    state = transition(state, GameAction.hop("h1", Point(5, 5))).state
    state = transition(state, GameAction.pickup_stone()).state
    return transition(state, GameAction.complete_house()).state


def test_facing_selection_successfully_claims_completed_house() -> None:
    state = claim_selection_state()
    state = transition(state, GameAction.select_claim("h1", ClaimSelectionMode.FACING)).state
    state = transition(state, GameAction.resolve_claim(True)).state

    assert state.ownership == {"h1": "p1"}
    assert state.claim.selection_mode is ClaimSelectionMode.FACING
    assert state.claim.successful is True
    assert state.scores == {"p1": 1, "p2": 0}
    assert state.score_for("p1") == 1
    assert state.phase is GamePhase.NEXT_HOUSE


def test_back_facing_selection_is_supported() -> None:
    state = claim_selection_state()
    state = transition(state, GameAction.select_claim("h1", "back_facing")).state

    assert state.claim.selection_mode is ClaimSelectionMode.BACK_FACING


def test_invalid_selection_mode_is_rejected() -> None:
    state = claim_selection_state()

    with pytest.raises(InvalidTransitionError, match="facing or back_facing"):
        transition(state, GameAction.select_claim("h1", "sideways"))


def test_selected_house_must_be_the_completed_house() -> None:
    state = claim_selection_state()

    with pytest.raises(InvalidTransitionError, match="completed house"):
        transition(state, GameAction.select_claim("h2", "facing"))


def test_occupied_house_cannot_be_claimed() -> None:
    state = claim_selection_state()
    state = GameState(**{**state.__dict__, "ownership": {"h1": "p2"}})

    with pytest.raises(InvalidTransitionError, match="already-owned"):
        transition(state, GameAction.select_claim("h1", "facing"))


def test_failed_claim_throw_does_not_award_ownership() -> None:
    state = claim_selection_state()
    state = transition(state, GameAction.select_claim("h1", "facing")).state
    state = transition(
        state,
        GameAction.resolve_claim(False, "claim_throw_failed"),
    ).state

    assert state.ownership == {}
    assert state.scores == {"p1": 0, "p2": 0}
    assert state.claim.successful is False
    assert state.claim.failure_reason == "claim_throw_failed"
    assert state.phase is GamePhase.TURN_END


def test_claim_boundary_failure_does_not_award_ownership() -> None:
    state = claim_selection_state()
    state = transition(state, GameAction.select_claim("h1", "back_facing")).state
    state = transition(
        state,
        GameAction.resolve_claim(False, "boundary_touched"),
    ).state

    assert state.ownership == {}
    assert state.claim.failure_reason == "boundary_touched"
    assert state.claim.successful is False


def test_ownership_persists_after_transition_to_next_house() -> None:
    state = claim_selection_state()
    state = transition(state, GameAction.select_claim("h1", "facing")).state
    state = transition(state, GameAction.resolve_claim(True)).state
    state = transition(state, GameAction.next_house()).state

    assert state.ownership == {"h1": "p1"}
    assert state.scores["p1"] == 1
    assert state.scores["p2"] == 0


def test_failed_claim_waits_until_next_round_by_default() -> None:
    state = claim_selection_state()
    state = transition(state, GameAction.select_claim("h1", "facing")).state
    state = transition(state, GameAction.resolve_claim(False, "boundary_touched")).state

    assert state.claim_retry_until_round == {"p1": 2}
    assert state.can_attempt_claim("p1") is False

    next_round = GameState(**{**state.__dict__, "round": RoundState(number=2)})
    assert next_round.can_attempt_claim("p1") is True


def test_claim_retry_timing_is_configurable() -> None:
    state = claim_selection_state(GameConfig(claim_retry_rounds=0))
    state = transition(state, GameAction.select_claim("h1", "facing")).state
    state = transition(state, GameAction.resolve_claim(False, "claim_throw_failed")).state

    assert state.claim_retry_until_round == {"p1": 1}
    assert state.can_attempt_claim("p1") is True


def test_score_is_derived_from_ownership() -> None:
    state = GameState(
        **{
            **make_state().__dict__,
            "ownership": {"h1": "p1", "h2": "p1", "h3": "p2"},
        }
    )

    assert state.scores == {"p1": 2, "p2": 1}
    assert state.score_for("p1") == 2
    assert state.score_for("p2") == 1

    with pytest.raises(ValueError, match="unknown player"):
        state.score_for("missing")


def test_claim_success_is_only_recorded_after_throw_resolution() -> None:
    state = claim_selection_state()
    state = transition(state, GameAction.select_claim("h1", "facing")).state

    assert state.ownership == {}
    assert state.phase is GamePhase.CLAIM_RESOLUTION

    state = transition(state, GameAction.resolve_claim(True)).state
    assert state.ownership == {"h1": "p1"}
