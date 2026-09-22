from jumpup import (
    Bounds,
    House,
    Layout,
    LayoutType,
    Point,
    run_batch,
    simulate_game,
)
from jumpup.simulation import HumanLikeActionProvider, RandomActionProvider, RuleBasedActionProvider
from jumpup.geometry import HouseGeometry


def make_layout(count: int = 3) -> Layout:
    houses = []
    for index in range(count):
        x = float(index * 10)
        geometry = HouseGeometry(
            boundary=(
                Point(x, 0),
                Point(x + 10, 0),
                Point(x + 10, 10),
                Point(x, 10),
                Point(x, 0),
            ),
            bounds=Bounds(x, 0, x + 10, 10),
        )
        houses.append(
            House(
                id=f"h{index + 1}",
                number=index + 1,
                sequence_index=index,
                geometry=geometry,
            )
        )
    return Layout(id="simulation-test", type=LayoutType.SQUARE, houses=tuple(houses))


def test_rule_based_provider_completes_headless_game() -> None:
    result = simulate_game(make_layout(), player_count=2, seed=7)

    assert result.completed is True
    assert result.winner == "player-1"
    assert result.final_scores == {"player-1": 3, "player-2": 0}
    assert result.failed_throws == 0
    assert result.failed_hops == 0
    assert result.failed_claims == 0
    assert result.action_counts["throw"] == 3
    assert result.turns == result.action_counts["begin_turn"] == 3


def test_simulation_is_reproducible_for_same_seed() -> None:
    factory = lambda _player_id, rng: RandomActionProvider(rng, error_rate=0.15)

    first = simulate_game(make_layout(), player_count=2, seed=123, provider_factory=factory)
    second = simulate_game(make_layout(), player_count=2, seed=123, provider_factory=factory)

    assert first.to_dict() == second.to_dict()


def test_human_like_provider_is_supported() -> None:
    factory = lambda _player_id, rng: HumanLikeActionProvider(rng, error_rate=0.05)
    result = simulate_game(make_layout(2), player_count=2, seed=4, provider_factory=factory)

    assert result.completed is True
    assert result.player_count == 2
    assert result.action_counts["begin_turn"] >= 1


def test_batch_collects_metrics_and_throughput() -> None:
    result = run_batch(make_layout(2), games=5, player_count=2, seed=20)

    assert len(result.games) == 5
    assert result.games_per_second > 0
    assert result.completion_rate == 1.0
    assert result.to_dict()["games"] == 5
