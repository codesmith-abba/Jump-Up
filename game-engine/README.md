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
