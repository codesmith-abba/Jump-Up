"""Deterministic authoritative state transitions for Jump-Up."""

from collections.abc import Callable
from dataclasses import dataclass, replace

from .actions import GameAction, GameActionType
from .model import (
    ClaimState,
    GamePhase,
    GameState,
    RoundState,
    TurnState,
    WinnerState,
)
from .movement import (
    MovementValidationError,
    begin_hopping,
    begin_return,
    can_pickup_stone,
    hop,
)


class InvalidTransitionError(ValueError):
    """Raised when an action is not legal for the current model phase."""


@dataclass(frozen=True)
class TransitionResult:
    state: GameState
    action: GameAction


def _require_phase(state: GameState, *phases: GamePhase) -> None:
    if state.phase not in phases:
        allowed = ", ".join(phase.value for phase in phases)
        raise InvalidTransitionError(
            f"action is invalid in phase {state.phase.value}; expected one of: {allowed}"
        )


def _require_player(state: GameState, player_id: str | None) -> str:
    if player_id is None or player_id not in {player.id for player in state.players}:
        raise InvalidTransitionError(f"unknown player: {player_id}")
    return player_id


def _current_turn(state: GameState) -> TurnState:
    if state.turn is None:
        raise InvalidTransitionError("current turn is not initialized")
    if state.current_player_id != state.turn.player_id:
        raise InvalidTransitionError("turn player is not the current player")
    return state.turn


def _start_game(state: GameState) -> GameState:
    _require_phase(state, GamePhase.SETUP)
    if len(state.players) < state.config.min_players:
        raise InvalidTransitionError(
            f"at least {state.config.min_players} players are required to start"
        )
    first_player = min(state.players, key=lambda player: player.order)
    return replace(state, current_player_id=first_player.id, phase=GamePhase.TURN_START)


def _begin_turn(state: GameState, player_id: str | None) -> GameState:
    _require_phase(state, GamePhase.TURN_START)
    current_player_id = _require_player(state, player_id or state.current_player_id)
    if current_player_id != state.current_player_id:
        raise InvalidTransitionError("cannot begin a turn for a non-current player")
    player = next(player for player in state.players if player.id == current_player_id)
    stone = next(stone for stone in state.stones if stone.id == player.stone_id)
    target = (
        state.turn.current_house_id
        if state.turn is not None and state.turn.player_id == current_player_id
        else state.layout.first_house_id
    )
    turn = TurnState(
        player_id=current_player_id,
        current_house_id=target,
        target_house_id=target,
        stone_id=stone.id,
    )
    return replace(state, phase=GamePhase.THROW, turn=turn)


def _throw(state: GameState, house_id: str | None) -> GameState:
    _require_phase(state, GamePhase.THROW)
    if house_id is None:
        raise InvalidTransitionError("throw requires a target house")
    turn = _current_turn(state)
    if house_id != turn.target_house_id:
        raise InvalidTransitionError("throw target must be the current target house")
    return replace(state, phase=GamePhase.THROW_RESOLUTION)


def _resolve_throw(state: GameState, action: GameAction) -> GameState:
    _require_phase(state, GamePhase.THROW_RESOLUTION)
    if action.success is None:
        raise InvalidTransitionError("throw resolution requires success")
    turn = _current_turn(state)
    if not action.success:
        return replace(
            state,
            phase=GamePhase.TURN_END,
            turn=replace(
                turn,
                failed=True,
                failure_reason=action.failure_reason or "invalid_throw",
            ),
        )
    stones = tuple(
        replace(stone, location_house_id=turn.target_house_id, in_hand=False)
        if stone.id == turn.stone_id
        else stone
        for stone in state.stones
    )
    return replace(state, phase=GamePhase.HOPPING_OUT, stones=stones)


def _begin_hopping_out(state: GameState, movement_path: tuple[str, ...] | None) -> GameState:
    _require_phase(state, GamePhase.HOPPING_OUT)
    if movement_path is None:
        raise InvalidTransitionError(
            "begin_hopping_out requires an explicit layout-specific movement path"
        )
    turn = _current_turn(state)
    try:
        movement = begin_hopping(
            state.layout,
            turn.target_house_id,
            movement_path,
        )
    except MovementValidationError as exc:
        return _movement_failure(state, str(exc))
    return replace(state, turn=replace(turn, movement=movement))


def _movement_failure(state: GameState, reason: str) -> GameState:
    turn = _current_turn(state)
    return replace(
        state,
        phase=GamePhase.TURN_END,
        turn=replace(turn, failed=True, failure_reason=reason),
    )


def _hop(state: GameState, action: GameAction) -> GameState:
    _require_phase(state, GamePhase.HOPPING_OUT, GamePhase.HOPPING_BACK)
    turn = _current_turn(state)
    if turn.movement is None:
        raise InvalidTransitionError("hopping has not been initialized")
    if action.house_id is None or action.position is None:
        raise InvalidTransitionError("hop requires destination house and position")
    try:
        movement = hop(
            turn.movement,
            state.layout,
            action.house_id,
            action.position,
            feet=action.feet,
            ownership=state.ownership,
            player_id=turn.player_id,
        )
    except MovementValidationError as exc:
        return _movement_failure(state, str(exc))
    return replace(state, turn=replace(turn, movement=movement))


def _begin_hopping_back(state: GameState) -> GameState:
    _require_phase(state, GamePhase.HOPPING_OUT)
    turn = _current_turn(state)
    if turn.movement is None:
        raise InvalidTransitionError("hopping has not been initialized")
    try:
        movement = begin_return(turn.movement)
    except MovementValidationError as exc:
        return _movement_failure(state, str(exc))
    return replace(state, phase=GamePhase.HOPPING_BACK, turn=replace(turn, movement=movement))


def _pickup_stone(state: GameState) -> GameState:
    _require_phase(state, GamePhase.STONE_PICKUP, GamePhase.HOPPING_BACK)
    turn = _current_turn(state)
    if turn.movement is None or not can_pickup_stone(turn.movement):
        return _movement_failure(state, "stone_pickup_requires_one_leg_return_to_target")
    stones = tuple(
        replace(stone, location_house_id=None, in_hand=True) if stone.id == turn.stone_id else stone
        for stone in state.stones
    )
    return replace(state, phase=GamePhase.HOUSE_COMPLETED, stones=stones)


def _complete_house(state: GameState) -> GameState:
    _require_phase(state, GamePhase.HOUSE_COMPLETED)
    turn = _current_turn(state)
    return replace(
        state,
        phase=GamePhase.CLAIM_SELECTION,
        turn=replace(turn, completed_house_id=turn.current_house_id),
    )


def _select_claim(state: GameState, action: GameAction) -> GameState:
    _require_phase(state, GamePhase.CLAIM_SELECTION)
    if action.house_id is None or action.selection_mode is None:
        raise InvalidTransitionError("claim selection requires house_id and selection_mode")
    if action.house_id not in state.layout_ids:
        raise InvalidTransitionError("claim house must exist")
    if action.house_id in state.ownership:
        raise InvalidTransitionError("already-owned house cannot be selected")
    player_id = state.current_player_id
    if player_id is None:
        raise InvalidTransitionError("claim selection requires a current player")
    claim = ClaimState(
        selected_house_id=action.house_id,
        selected_player_id=player_id,
        selection_mode=action.selection_mode,
    )
    return replace(state, phase=GamePhase.CLAIM_RESOLUTION, claim=claim)


def _resolve_claim(state: GameState, success: bool | None) -> GameState:
    _require_phase(state, GamePhase.CLAIM_RESOLUTION)
    if success is None:
        raise InvalidTransitionError("claim resolution requires success")
    claim = state.claim
    if claim.selected_house_id is None or claim.selected_player_id is None:
        raise InvalidTransitionError("cannot resolve an empty claim")
    ownership = dict(state.ownership)
    if success:
        if claim.selected_house_id in ownership:
            raise InvalidTransitionError("already-owned house cannot be claimed")
        ownership[claim.selected_house_id] = claim.selected_player_id
    resolved = replace(claim, resolved=True, successful=success)
    return replace(
        state,
        phase=GamePhase.NEXT_HOUSE if success else GamePhase.TURN_END,
        ownership=ownership,
        claim=resolved,
    )


def _next_house(state: GameState) -> GameState:
    _require_phase(state, GamePhase.NEXT_HOUSE)
    turn = _current_turn(state)
    next_house = state.layout.next_house_id(turn.current_house_id)
    if next_house is None:
        return replace(state, phase=GamePhase.TURN_END)
    updated_turn = replace(
        turn,
        current_house_id=next_house,
        target_house_id=next_house,
        completed_house_id=None,
        movement=None,
    )
    return replace(state, phase=GamePhase.TURN_START, turn=updated_turn)


def _end_turn(state: GameState) -> GameState:
    _require_phase(state, GamePhase.TURN_END)
    return replace(
        state,
        phase=GamePhase.NEXT_PLAYER,
        round=RoundState(
            number=state.round.number,
            completed_turns=state.round.completed_turns + 1,
        ),
    )


def _next_player(state: GameState) -> GameState:
    _require_phase(state, GamePhase.NEXT_PLAYER)
    ordered = sorted(state.players, key=lambda player: player.order)
    current_index = next(
        (index for index, player in enumerate(ordered) if player.id == state.current_player_id),
        -1,
    )
    next_index = (current_index + 1) % len(ordered)
    return replace(
        state,
        current_player_id=ordered[next_index].id,
        phase=GamePhase.TURN_START,
        turn=None,
        claim=ClaimState(),
    )


def _end_game(state: GameState, player_id: str | None) -> GameState:
    _require_phase(
        state,
        GamePhase.TURN_START,
        GamePhase.TURN_END,
        GamePhase.NEXT_PLAYER,
        GamePhase.HOUSE_COMPLETED,
        GamePhase.NEXT_HOUSE,
    )
    if player_id is not None:
        _require_player(state, player_id)
    return replace(
        state,
        phase=GamePhase.GAME_OVER,
        winner=WinnerState(player_id=player_id, is_final=True),
    )


def transition(state: GameState, action: GameAction) -> TransitionResult:
    """Apply exactly one explicit state transition deterministically."""
    handlers: dict[GameActionType, Callable[[], GameState]] = {
        GameActionType.START_GAME: lambda: _start_game(state),
        GameActionType.BEGIN_TURN: lambda: _begin_turn(state, action.player_id),
        GameActionType.THROW: lambda: _throw(state, action.house_id),
        GameActionType.RESOLVE_THROW: lambda: _resolve_throw(state, action),
        GameActionType.BEGIN_HOPPING_OUT: lambda: _begin_hopping_out(state, action.movement_path),
        GameActionType.HOP: lambda: _hop(state, action),
        GameActionType.BEGIN_HOPPING_BACK: lambda: _begin_hopping_back(state),
        GameActionType.PICKUP_STONE: lambda: _pickup_stone(state),
        GameActionType.COMPLETE_HOUSE: lambda: _complete_house(state),
        GameActionType.SELECT_CLAIM: lambda: _select_claim(state, action),
        GameActionType.RESOLVE_CLAIM: lambda: _resolve_claim(state, action.success),
        GameActionType.NEXT_HOUSE: lambda: _next_house(state),
        GameActionType.END_TURN: lambda: _end_turn(state),
        GameActionType.NEXT_PLAYER: lambda: _next_player(state),
        GameActionType.END_GAME: lambda: _end_game(state, action.player_id),
    }
    try:
        next_state = handlers[action.type]()
    except KeyError as exc:
        raise InvalidTransitionError(f"unsupported action: {action.type}") from exc
    return TransitionResult(state=next_state, action=action)
