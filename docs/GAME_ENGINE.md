# Jump-Up Game Engine

## Purpose

The game engine is the single authoritative source of Jump-Up game state. It is renderer-independent and deterministic, and is intended to be reusable by human gameplay, AI, simulations, automated tests, and the future mobile renderer.

It is intentionally independent of React Native, Expo, Pygame, networking, and animation.

## Phase 2–6 foundation

The authoritative snapshot is `GameState`. It contains the selected layout, ordered houses, players, stones, current player, turn state, round state, ownership, claim state, winner state, configuration, and claim retry state.

The engine also contains deterministic geometry, stone physics, logical hopping/movement, and house claiming. These layers are connected only through explicit state transitions.

## Phase 7 — Complete game loop

Phase 7 connects the existing components into one complete UI-independent rules loop.

The authoritative lifecycle is:

```text
SETUP
  ↓
START_GAME
  ↓
TURN_START
  ↓
THROW
  ↓
THROW_RESOLUTION
  ├── failure → TURN_END → END_TURN → NEXT_PLAYER → TURN_START
  │
  └── success
       ↓
     HOPPING_OUT
       ↓
     HOPPING_BACK
       ↓
     STONE_PICKUP
       ↓
     HOUSE_COMPLETED
       ↓
     CLAIM_SELECTION
       ↓
     CLAIM_RESOLUTION
       ├── failure → TURN_END → END_TURN → NEXT_PLAYER
       │
       └── success
            ├── houses remain → NEXT_HOUSE → TURN_START (same player)
            └── all houses owned → GAME_OVER
```

### Turn start and target selection

`BEGIN_TURN` initializes the active player's turn. The player's current sequential house is the target. A new player starts at house 1; a player continuing after a successful claim advances to the next sequential house through `NEXT_HOUSE`.

`THROW` verifies that the submitted target is exactly the current target house. The actual throw result is supplied to `RESOLVE_THROW`. A successful result places the player's stone in the target house; a failed result ends the turn without progressing the player.

The Phase 4 physics system remains responsible for determining the actual throw result. The game loop consumes that result rather than duplicating physics.

### Hopping and return

`BEGIN_HOPPING_OUT` requires the explicit layout-specific path. The movement engine enforces the stone-house skip and validates every hop independently of rendering.

After the final required outbound house, `BEGIN_HOPPING_BACK` switches to the reverse path plus the stone house. `PICKUP_STONE` succeeds only when the player has returned to the target while still on one leg.

A movement violation transitions the current turn to `TURN_END`.

### House completion

After stone pickup, `COMPLETE_HOUSE` records the sequential house as completed and enters claim selection.

### Claiming

The claim flow is:

```text
CLAIM_SELECTION
    ↓
select completed eligible house + FACING/BACK_FACING
    ↓
CLAIM_RESOLUTION
    ↓
actual claim throw result
```

Selection does not award ownership. Ownership is awarded only after successful claim resolution.

An occupied house cannot be selected. A failed claim does not award ownership and applies the configured claim retry timing.

### Sequential progression

After a successful claim, `NEXT_HOUSE` advances the same player's sequential target by one house.

For an eight-house layout the intended sequence is therefore:

```text
H1 → H2 → H3 → H4 → H5 → H6 → H7 → H8
```

For target `Hn`, the movement path must explicitly omit `Hn`, traverse the required houses, return to `Hn`, and retrieve the stone.

If a throw, movement, or claim fails, the current turn ends. The next player receives the next turn. Failure does not remove the player or erase existing ownership.

### Rounds

A round advances after the last participating player completes their turn and control cycles back to the first player.

`completed_turns` counts ended turns within the current round. This round definition is authoritative for claim retry timing.

### Game completion

Phase 7 finalizes the previously unresolved ending condition as:

> **The game ends when every house in the selected layout has an owner.**

This is evaluated immediately after a successful claim. No additional turn is required once the final unclaimed house has been successfully claimed.

The existing manual `END_GAME` action remains available for deterministic test/control use, but normal gameplay reaches `GAME_OVER` automatically through successful final claim resolution.

### Winner calculation

At `GAME_OVER` the engine calculates:

```text
score(player) = number of houses owned by player
```

The player with the highest score is the winner.

If multiple players have the same highest score, `WinnerState.tied_player_ids` contains all tied leaders in deterministic player-ID order and `winner.player_id` is `None`.

No score counter is stored separately from ownership; scores are derived from the authoritative ownership mapping.

## Complete UI-independent execution

A complete game can be executed without any UI by repeatedly passing `GameAction` objects through:

```python
result = transition(state, action)
state = result.state
```

The integration tests in `game-engine/tests/test_game_loop.py` exercise:

- game start;
- target selection;
- successful throw;
- outbound hopping;
- return traversal;
- stone retrieval;
- house completion;
- claim resolution;
- sequential house advancement;
- turn failure;
- next-player progression;
- round advancement;
- automatic game completion;
- winner calculation.

The UI will later translate human input and animation into these same authoritative actions; it will not implement a second game loop.

## Rendering separation

The engine does not know about Pygame, React Native, Expo, sprites, animation frames, gestures, or frame rate. A renderer can visualize the state and animate legal actions, but cannot change the authoritative rules result.

## Phase 7 non-goals

Phase 7 does not implement:

- AI strategy;
- AI gameplay;
- React Native integration;
- Pygame integration;
- multiplayer networking;
- UI animation;
- new physics behavior.


## Phase 9 — Headless simulation

The `game-engine/src/jumpup/simulation.py` module provides a headless execution layer over the authoritative game engine.

The simulator:

- accepts any valid `Layout`;
- supports 2–4 players;
- uses deterministic seeds;
- delegates decisions to an `ActionProvider`;
- applies all game actions through `transition()`;
- collects per-game metrics;
- runs batches and reports throughput;
- has no rendering or UI dependency.

### Provider boundary

```text
ActionProvider
    ├── RuleBasedActionProvider
    ├── RandomActionProvider
    ├── HumanLikeActionProvider
    └── Future trained AI
```

The provider sees the authoritative `GameState` and returns decisions for throwing, movement, hopping, and claiming. This is the interface a future trained model will replace; the rules engine does not need to change.

### Metrics

`SimulationResult` records:

- winner and tied players;
- claimed houses / final scores;
- failed throws;
- failed hops;
- failed claims;
- turns;
- rounds;
- simulated physics duration;
- action counts;
- deterministic seed.

`BatchResult` adds completion rate, winner counts, averages, wall-clock execution time, and games-per-second throughput.

### Batch and benchmark

The installed `jumpup-sim` command can run one game, batches, or a benchmark:

```bash
jumpup-sim --layout "../Python (Pygame)/houses/heart.txt" --players 2 --games 1000 --seed 42 --provider random
jumpup-sim --layout "../Python (Pygame)/houses/heart.txt" --players 2 --games 10000 --benchmark
```

Phase 9 does not train an ML model. Its output is the execution and statistics foundation for future training-data generation and evaluation.
