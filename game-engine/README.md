# Jump-Up Game Engine

The game-engine package is the authoritative, UI-independent state model for Jump-Up.

## Phase 2 scope

This phase establishes:

- explicit typed domain state for games, layouts, houses, players, stones, turns, rounds, ownership, claims, and winners;
- explicit GamePhase values instead of scattered lifecycle booleans;
- deterministic, single-action state transitions;
- invalid-transition errors;
- JSON-compatible state serialization;
- unit tests for the foundational model.

This is intentionally not yet the complete gameplay engine. Geometry, movement/foot validation, throw physics, and the complete traditional-game rules are implemented in later phases.

## Dependency boundary

The package has no React Native, Expo, Pygame, AI, or UI dependency.

Consumers should treat GameState as authoritative and use transition(state, action) rather than mutating state directly.


## Phase 10 — First AI opponent

The first AI is a rule-based baseline built directly on the authoritative game engine.

### AI interface

JumpUpAI receives the current GameState and selects:

- target house;
- throw position;
- movement path;
- hop landing and foot count;
- claim selection mode.

The AI never mutates GameState and never resolves engine outcomes itself. Every selected action is passed to transition() by the simulator, which remains authoritative.

### Baseline strategy

RuleBasedActionProvider uses deterministic, low-risk heuristics:

- select the target already assigned by the current turn;
- throw at the target house center;
- traverse every required house except the target;
- land at house centers;
- use one foot on the target during return so the stone can be picked up;
- use two feet on houses already owned by the current player where the movement rules allow it;
- select a facing claim;
- let the engine determine whether movement, throw, pickup, or claim resolution succeeds.

RandomActionProvider provides the randomized mode. It uses a seeded RNG to introduce controlled throw, movement, hop, and claim imperfections while using the same AI interface.

### Evaluation

Deterministic baseline:

```bash
jumpup-sim --layout "../Python (Pygame)/houses/heart.txt" --players 2 --games 10 --seed 42 --provider rule
```

Randomized baseline:

```bash
jumpup-sim --layout "../Python (Pygame)/houses/heart.txt" --players 2 --games 100 --seed 42 --provider random
```

The correctness property is that AI decisions are proposals only. transition() remains the only component that changes authoritative game state.

## Phase 9 — Headless simulation

The `jumpup.simulation` module runs games directly against the authoritative `transition()` engine without React Native, Expo, Pygame, rendering, UI input, animation, or ML frameworks.

### Providers

The `ActionProvider` protocol supports four intended agent types:

- `RuleBasedActionProvider` — deterministic legal baseline.
- `RandomActionProvider` — seeded stochastic baseline.
- `HumanLikeActionProvider` — seeded imperfect-play baseline.
- Future trained AI — implement the same protocol.

Providers choose throws, movement paths, hop landings, and claim outcomes. The simulator remains responsible for executing those choices through the authoritative engine.

### CLI

Run one game:

```bash
jumpup-sim --layout "../Python (Pygame)/houses/heart.txt" --players 2 --seed 42 --provider rule
```

Run a batch:

```bash
jumpup-sim --layout "../Python (Pygame)/houses/heart.txt" --players 2 --games 1000 --seed 42 --provider random
```

Benchmark throughput:

```bash
jumpup-sim --layout "../Python (Pygame)/houses/heart.txt" --players 2 --games 10000 --benchmark
```

The benchmark reports wall-clock time and `games_per_second`. It does not train a model.

### Metrics

Each game records the winner, tied leaders, claimed houses per player, failed throws, failed hops, failed claims, turns, rounds, simulated physics duration, action counts, final scores, and seed.

Batch results additionally report completion rate, winner counts, average turns and rounds, average game duration, total failures, wall-clock time, and games per second.

### Deterministic AI-training boundary

A fixed seed plus the same provider configuration produces the same simulation decisions and result. Every action still passes through `transition()`; the simulator never mutates authoritative state directly.

Phase 9 deliberately does not train a machine-learning model. It establishes the execution loop that future training can consume:

```text
GameState → ActionProvider → transition() → SimulationResult → batch statistics
```


## Phase 11 — AI training environment

The formal learning boundary is implemented in jumpup.ai_environment and documented in docs/AI_SPEC.md.
