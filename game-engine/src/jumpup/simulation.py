"""Headless game simulation and AI-provider interfaces for Jump-Up.

The simulator is deliberately built on top of the authoritative transition
function. It never renders, sleeps, or depends on Pygame/React Native.
"""

from __future__ import annotations

import argparse
import json
import random
import time
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .actions import GameAction
from .layouts import load_legacy_layout
from .model import ClaimSelectionMode, GamePhase, GameState, Layout, Player, Point, Stone
from .physics import StoneInitialState, simulate_throw
from .transition import transition


@dataclass(frozen=True)
class ThrowDecision:
    """A provider's physical throw proposal."""

    position: Point
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_z: float = 0.0
    height: float = 0.0


@dataclass(frozen=True)
class HopDecision:
    """A provider's landing choice for one logical hop."""

    position: Point
    feet: int = 1


@dataclass(frozen=True)
class ClaimDecision:
    """A provider's house-claim choice and outcome."""

    selection_mode: ClaimSelectionMode = ClaimSelectionMode.FACING
    success: bool = True
    failure_reason: str | None = None


class ActionProvider(Protocol):
    """Interface implemented by human, random, rule-based, and trained AI agents."""

    def choose_throw(self, state: GameState) -> ThrowDecision: ...

    def choose_movement_path(self, state: GameState) -> tuple[str, ...]: ...

    def choose_hop(self, state: GameState, house_id: str) -> HopDecision: ...

    def choose_claim(self, state: GameState) -> ClaimDecision: ...


@dataclass(frozen=True)
class SimulationResult:
    """Deterministic game-level metrics plus action telemetry."""

    seed: int
    layout_id: str
    player_count: int
    winner: str | None
    tied_players: tuple[str, ...]
    claimed_houses: dict[str, int]
    failed_throws: int
    failed_hops: int
    failed_claims: int
    turns: int
    rounds: int
    game_duration_seconds: float
    action_counts: dict[str, int]
    final_scores: dict[str, int]
    completed: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "layout_id": self.layout_id,
            "player_count": self.player_count,
            "winner": self.winner,
            "tied_players": list(self.tied_players),
            "claimed_houses": dict(self.claimed_houses),
            "failed_throws": self.failed_throws,
            "failed_hops": self.failed_hops,
            "failed_claims": self.failed_claims,
            "turns": self.turns,
            "rounds": self.rounds,
            "game_duration_seconds": self.game_duration_seconds,
            "action_counts": dict(self.action_counts),
            "final_scores": dict(self.final_scores),
            "completed": self.completed,
        }


@dataclass(frozen=True)
class BatchResult:
    """Aggregate metrics for a batch of independent simulations."""

    games: tuple[SimulationResult, ...]
    wall_time_seconds: float
    games_per_second: float

    @property
    def winner_counts(self) -> dict[str, int]:
        counts: Counter[str] = Counter()
        for game in self.games:
            if game.winner is not None:
                counts[game.winner] += 1
            elif game.tied_players:
                counts["tie"] += 1
        return dict(counts)

    @property
    def completion_rate(self) -> float:
        return (
            sum(game.completed for game in self.games) / len(self.games)
            if self.games
            else 0.0
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "games": len(self.games),
            "wall_time_seconds": self.wall_time_seconds,
            "games_per_second": self.games_per_second,
            "completion_rate": self.completion_rate,
            "winner_counts": self.winner_counts,
            "average_turns": _average(game.turns for game in self.games),
            "average_rounds": _average(game.rounds for game in self.games),
            "average_game_duration_seconds": _average(
                game.game_duration_seconds for game in self.games
            ),
            "total_failed_throws": sum(game.failed_throws for game in self.games),
            "total_failed_hops": sum(game.failed_hops for game in self.games),
            "total_failed_claims": sum(game.failed_claims for game in self.games),
        }


def _average(values: Iterable[float]) -> float:
    numbers = list(values)
    return sum(numbers) / len(numbers) if numbers else 0.0


def _center(house) -> Point:
    return house.geometry.center


def _safe_hop_decision(state: GameState, house_id: str) -> HopDecision:
    house = next(house for house in state.layout.houses if house.id == house_id)
    feet = 2 if state.ownership.get(house_id) == state.current_player_id else 1
    return HopDecision(position=_center(house), feet=feet)


def _make_players(player_count: int) -> tuple[Player, ...]:
    players = []
    stones = []
    for index in range(player_count):
        player_id = f"player-{index + 1}"
        stone_id = f"stone-{index + 1}"
        players.append(
            Player(id=player_id, name=f"Player {index + 1}", stone_id=stone_id, order=index)
        )
        stones.append(Stone(id=stone_id, owner_id=player_id))
    return tuple(players), tuple(stones)


class RuleBasedActionProvider:
    """Always chooses legal, low-risk actions using house geometry."""

    def choose_throw(self, state: GameState) -> ThrowDecision:
        target_id = state.turn.target_house_id  # type: ignore[union-attr]
        target = next(h for h in state.layout.houses if h.id == target_id)
        return ThrowDecision(position=_center(target))

    def choose_movement_path(self, state: GameState) -> tuple[str, ...]:
        target = state.turn.target_house_id  # type: ignore[union-attr]
        return tuple(h.id for h in state.layout.houses if h.id != target)

    def choose_hop(self, state: GameState, house_id: str) -> HopDecision:
        return _safe_hop_decision(state, house_id)

    def choose_claim(self, state: GameState) -> ClaimDecision:
        return ClaimDecision(selection_mode=ClaimSelectionMode.FACING, success=True)


class RandomActionProvider:
    """Seeded stochastic provider suitable for baseline simulation experiments."""

    def __init__(self, rng: random.Random, error_rate: float = 0.25) -> None:
        if not 0.0 <= error_rate <= 1.0:
            raise ValueError("error_rate must be between 0 and 1")
        self.rng = rng
        self.error_rate = error_rate

    def choose_throw(self, state: GameState) -> ThrowDecision:
        target = next(
            h for h in state.layout.houses if h.id == state.turn.target_house_id  # type: ignore[union-attr]
        )
        if self.rng.random() < self.error_rate:
            bounds = target.geometry.bounds
            return ThrowDecision(
                position=Point(
                    self.rng.uniform(bounds.min_x - 1.0, bounds.max_x + 1.0),
                    self.rng.uniform(bounds.min_y - 1.0, bounds.max_y + 1.0),
                )
            )
        return ThrowDecision(position=_center(target))

    def choose_movement_path(self, state: GameState) -> tuple[str, ...]:
        target = state.turn.target_house_id  # type: ignore[union-attr]
        houses = [h.id for h in state.layout.houses if h.id != target]
        if self.rng.random() < self.error_rate and houses:
            houses.reverse()
        return tuple(houses)

    def choose_hop(self, state: GameState, house_id: str) -> HopDecision:
        decision = _safe_hop_decision(state, house_id)
        if self.rng.random() >= self.error_rate:
            return decision
        house = next(h for h in state.layout.houses if h.id == house_id)
        bounds = house.geometry.bounds
        return HopDecision(
            position=Point(
                self.rng.uniform(bounds.min_x - 0.5, bounds.max_x + 0.5),
                self.rng.uniform(bounds.min_y - 0.5, bounds.max_y + 0.5),
            ),
            feet=decision.feet,
        )

    def choose_claim(self, state: GameState) -> ClaimDecision:
        success = self.rng.random() >= self.error_rate
        return ClaimDecision(
            selection_mode=self.rng.choice(
                (ClaimSelectionMode.FACING, ClaimSelectionMode.BACK_FACING)
            ),
            success=success,
            failure_reason=None if success else "random_claim_failure",
        )


class HumanLikeActionProvider(RandomActionProvider):
    """A conservative stochastic provider approximating imperfect human play."""

    def __init__(self, rng: random.Random, error_rate: float = 0.08) -> None:
        super().__init__(rng, error_rate=error_rate)


def _valid_area(layout: Layout):
    bounds = [house.geometry.bounds for house in layout.houses]
    return type(bounds[0])(
        min(bound.min_x for bound in bounds),
        min(bound.min_y for bound in bounds),
        max(bound.max_x for bound in bounds),
        max(bound.max_y for bound in bounds),
    )


def _resolve_throw(
    state: GameState,
    decision: ThrowDecision,
) -> tuple[bool, str | None, float]:
    target_id = state.turn.target_house_id  # type: ignore[union-attr]
    target = next(h for h in state.layout.houses if h.id == target_id)
    result = simulate_throw(
        StoneInitialState(
            position=decision.position,
            height=decision.height,
            velocity_x=decision.velocity_x,
            velocity_y=decision.velocity_y,
            velocity_z=decision.velocity_z,
        ),
        target_house_id=target_id,
        target_house=target.geometry,
        valid_area=_valid_area(state.layout),
    )
    return result.throw_succeeded, result.status.value, result.state.elapsed_time


def _apply(state: GameState, action: GameAction) -> GameState:
    return transition(state, action).state


def simulate_game(
    layout: Layout,
    *,
    player_count: int = 2,
    seed: int = 0,
    provider_factory=None,
    max_turns: int = 10_000,
) -> SimulationResult:
    """Run one complete headless game against the authoritative engine."""

    if player_count < 2:
        raise ValueError("player_count must be at least 2")
    if player_count > 4:
        raise ValueError("player_count must not exceed 4")
    if max_turns < 1:
        raise ValueError("max_turns must be positive")

    players, stones = _make_players(player_count)
    state = GameState.initial(layout, players, stones)
    rng = random.Random(seed)
    factory = provider_factory or (lambda player_id, player_rng: RuleBasedActionProvider())
    providers = {
        player.id: factory(player.id, random.Random(rng.randrange(2**63)))
        for player in players
    }

    state = _apply(state, GameAction.start_game())
    action_counts: Counter[str] = Counter()
    failed_throws = 0
    failed_hops = 0
    failed_claims = 0
    turns = 0
    simulated_duration = 0.0

    while state.phase is not GamePhase.GAME_OVER:
        if turns >= max_turns:
            raise RuntimeError("simulation exceeded max_turns; provider or engine may be stuck")

        current_player = state.current_player_id
        if current_player is None:
            raise RuntimeError("engine reached a phase without a current player")
        provider = providers[current_player]

        if state.phase is GamePhase.TURN_START:
            state = _apply(state, GameAction.begin_turn(current_player))
            action_counts["begin_turn"] += 1
            continue

        if state.phase is GamePhase.THROW:
            decision = provider.choose_throw(state)
            state = _apply(state, GameAction.throw(state.turn.target_house_id))  # type: ignore[union-attr]
            action_counts["throw"] += 1
            success, reason, duration = _resolve_throw(state, decision)
            simulated_duration += duration
            if not success:
                failed_throws += 1
            state = _apply(state, GameAction.resolve_throw(success, reason))
            action_counts["resolve_throw"] += 1
            continue

        if state.phase is GamePhase.HOPPING_OUT:
            target = state.turn.target_house_id  # type: ignore[union-attr]
            # The current authoritative loop only permits claiming the
            # just-completed house. If another player already owns this target,
            # deliberately submit an invalid path so the engine records a
            # failed movement rather than bypassing authoritative state.
            if target in state.ownership and state.ownership[target] != current_player:
                path = (target,)
            else:
                path = provider.choose_movement_path(state)
            state = _apply(state, GameAction.begin_hopping_out(path))
            action_counts["begin_hopping_out"] += 1
            if state.phase is GamePhase.TURN_END:
                failed_hops += 1
            continue

        if state.phase in (GamePhase.HOPPING_OUT, GamePhase.HOPPING_BACK):
            movement = state.turn.movement  # type: ignore[union-attr]
            if movement is None:
                raise RuntimeError("movement phase has no movement state")
            sequence = (
                movement.required_outbound_house_ids
                if movement.direction.value == "outbound"
                else movement.return_house_ids
            )
            if movement.direction.value == "outbound" and not sequence:
                state = _apply(state, GameAction.begin_hopping_back())
                action_counts["begin_hopping_back"] += 1
                continue
            current = movement.current_house_id
            expected = sequence[0] if current is None else sequence[sequence.index(current) + 1]
            decision = provider.choose_hop(state, expected)
            state = _apply(
                state,
                GameAction.hop(expected, decision.position, feet=decision.feet),
            )
            action_counts["hop"] += 1
            if state.phase is GamePhase.TURN_END:
                failed_hops += 1
            elif movement.direction.value == "outbound" and expected == sequence[-1]:
                state = _apply(state, GameAction.begin_hopping_back())
                action_counts["begin_hopping_back"] += 1
            elif movement.direction.value == "return" and expected == sequence[-1]:
                state = _apply(state, GameAction.pickup_stone())
                action_counts["pickup_stone"] += 1
            continue

        if state.phase is GamePhase.STONE_PICKUP:
            state = _apply(state, GameAction.pickup_stone())
            action_counts["pickup_stone"] += 1
            continue

        if state.phase is GamePhase.HOUSE_COMPLETED:
            state = _apply(state, GameAction.complete_house())
            action_counts["complete_house"] += 1
            continue

        if state.phase is GamePhase.CLAIM_SELECTION:
            completed = state.turn.completed_house_id  # type: ignore[union-attr]
            decision = provider.choose_claim(state)
            state = _apply(state, GameAction.select_claim(completed, decision.selection_mode))
            action_counts["select_claim"] += 1
            state = _apply(
                state,
                GameAction.resolve_claim(decision.success, decision.failure_reason),
            )
            action_counts["resolve_claim"] += 1
            if not decision.success:
                failed_claims += 1
            continue

        if state.phase is GamePhase.NEXT_HOUSE:
            state = _apply(state, GameAction.next_house())
            action_counts["next_house"] += 1
            continue

        if state.phase is GamePhase.TURN_END:
            state = _apply(state, GameAction.end_turn())
            turns += 1
            action_counts["end_turn"] += 1
            continue

        if state.phase is GamePhase.NEXT_PLAYER:
            state = _apply(state, GameAction.next_player())
            action_counts["next_player"] += 1
            continue

        raise RuntimeError(f"unhandled engine phase: {state.phase.value}")

    scores = state.scores
    return SimulationResult(
        seed=seed,
        layout_id=layout.id,
        player_count=player_count,
        winner=state.winner.player_id,
        tied_players=state.winner.tied_player_ids,
        claimed_houses=dict(scores),
        failed_throws=failed_throws,
        failed_hops=failed_hops,
        failed_claims=failed_claims,
        turns=turns,
        rounds=state.round.number,
        game_duration_seconds=simulated_duration,
        action_counts=dict(action_counts),
        final_scores=dict(scores),
        completed=True,
    )


def run_batch(
    layout: Layout,
    *,
    games: int,
    player_count: int = 2,
    seed: int = 0,
    provider_factory=None,
    max_turns: int = 10_000,
) -> BatchResult:
    """Run many independent deterministic games and measure throughput."""

    if games < 1:
        raise ValueError("games must be positive")
    start = time.perf_counter()
    results = tuple(
        simulate_game(
            layout,
            player_count=player_count,
            seed=seed + index,
            provider_factory=provider_factory,
            max_turns=max_turns,
        )
        for index in range(games)
    )
    elapsed = time.perf_counter() - start
    return BatchResult(
        games=results,
        wall_time_seconds=elapsed,
        games_per_second=games / elapsed if elapsed else float("inf"),
    )


def benchmark(
    layout: Layout,
    *,
    games: int = 1_000,
    player_count: int = 2,
    seed: int = 0,
) -> dict[str, object]:
    """Benchmark the simulator without rendering or model training."""

    result = run_batch(
        layout,
        games=games,
        player_count=player_count,
        seed=seed,
        provider_factory=lambda _id, _rng: RuleBasedActionProvider(),
    )
    return result.to_dict()


def _provider_factory(name: str):
    if name == "rule":
        return lambda _id, _rng: RuleBasedActionProvider()
    if name == "random":
        return lambda _id, rng: RandomActionProvider(rng)
    if name == "human":
        return lambda _id, rng: HumanLikeActionProvider(rng)
    raise ValueError(f"unknown provider: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Headless Jump-Up simulator")
    parser.add_argument("--layout", required=True, help="Path to heart.txt, square.txt, or rect.txt")
    parser.add_argument("--players", type=int, default=2)
    parser.add_argument("--games", type=int, default=1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--provider", choices=("rule", "random", "human"), default="rule")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()

    layout = load_legacy_layout(Path(args.layout))
    factory = _provider_factory(args.provider)
    if args.benchmark:
        print(
            json.dumps(
                benchmark(
                    layout,
                    games=args.games,
                    player_count=args.players,
                    seed=args.seed,
                ),
                indent=2,
            )
        )
        return

    if args.games == 1:
        result = simulate_game(
            layout,
            player_count=args.players,
            seed=args.seed,
            provider_factory=factory,
        )
        print(json.dumps(result.to_dict(), indent=2))
        return

    result = run_batch(
        layout,
        games=args.games,
        player_count=args.players,
        seed=args.seed,
        provider_factory=factory,
    )
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
