# Jump-Up Game Engine

## Purpose

The game engine is the single authoritative source of Jump-Up game state. Phase 2 established the foundational model and deterministic lifecycle transition boundary. Phase 3 adds renderer-independent house geometry and production layout loading. Phase 4 adds deterministic stone physics. Phase 5 adds authoritative logical player movement and hopping validation.

It is intentionally independent of React Native, Expo, Pygame, AI, networking, and rendering.

## Phase 2 model

The authoritative snapshot is GameState. It contains:

- Layout: stable layout identity, layout type, and ordered houses.
- House: stable ID, sequential number, and sequence index.
- Player: stable ID, name, stone reference, and turn order.
- Stone: stable ID, owner, current house location, and hand state.
- TurnState: current player, current/target house, stone, completion/failure data, and movement state when hopping.
- RoundState: round number and completed-turn count.
- Ownership: house ID to player ID.
- ClaimState: selected house/player, selection mode, and claim result.
- WinnerState: final winner/tie information.
- GamePhase: explicit lifecycle phase.

The model uses typed Python dataclasses and enum values. No UI object is stored in game state.

## Lifecycle

The foundational lifecycle is:

SETUP
→ TURN_START
→ THROW
→ THROW_RESOLUTION
→ HOPPING_OUT
→ HOPPING_BACK
→ STONE_PICKUP
→ HOUSE_COMPLETED
→ CLAIM_SELECTION
→ CLAIM_RESOLUTION
→ NEXT_HOUSE
→ TURN_START

A failed throw or movement violation moves to TURN_END. A failed claim also moves to TURN_END. A completed turn moves through NEXT_PLAYER before another turn begins.

GAME_OVER is an explicit terminal phase with WinnerState.

## Transition API

Consumers submit one explicit GameAction to:

transition(GameState, GameAction) -> TransitionResult

The transition function checks the current phase, validates action data, creates a new GameState, leaves the input state unchanged, and returns the new state plus the applied action.

Invalid phase/action combinations raise InvalidTransitionError. A submitted gameplay movement violation is recorded as turn failure and transitions to TURN_END.

## Phase 5 — Player movement and hopping

Phase 5 adds `jumpup.movement`, the authoritative logical movement layer.

`MovementState` records:

- player position as the latest logical `Point`;
- current house;
- outbound/return direction;
- hopping/resting mode;
- one-leg state;
- thrown-stone target house;
- visited houses during the current movement sequence.

The movement implementation contains no rendering or animation concerns.

### Outbound movement

After a successful throw, `begin_hopping_out()` initializes one-leg hopping. The required outbound sequence is the layout's ordered houses with the stone/target house removed.

For a four-house layout with target house 2:

`1 → 3 → 4`

The target house is therefore skipped during outbound movement.

### Return movement

After all required outbound houses have been visited, `begin_hopping_back()` switches direction. The player then traverses the required houses in reverse order and finally lands in the stone house.

For the example above:

`4 → 3 → 1 → 2`

Stone retrieval is legal only after the player reaches the target house during this return movement, while still in one-leg hopping state.

### Foot rules

Normal movement uses one leg.

A two-foot landing/rest is accepted only when the destination house is owned by the active player. An attempt to use both feet in an unowned house is a movement violation and fails the turn.

After resting in an owned house, a subsequent valid hop continues the required sequence and returns the movement state to one-leg hopping.

### Boundary rules

A destination position must be strictly inside the destination house geometry. Boundary contact is rejected, and a position outside the destination house is rejected.

The existing renderer-independent geometry and Phase 4 boundary helpers are reused; no second boundary implementation was introduced.

### Movement failure

The transition layer records the validation error in `TurnState.failure_reason`, sets `TurnState.failed`, and moves the game to `TURN_END`. The player remains in the game, matching the established failure rule.

### Rendering separation

The movement layer does not know about Pygame, React Native, Expo, sprites, animation frames, gestures, or frame rate. A renderer can animate a legal movement, but it cannot change the authoritative legality result.

For the full movement state machine, see `docs/MOVEMENT_STATE_MACHINE.md`.

## Phase 4 — Deterministic stone physics

Phase 4 adds `jumpup.physics`, a renderer-independent deterministic stone throw simulator. It consumes the authoritative `HouseGeometry` and `Bounds` types, uses a fixed timestep, exposes configurable physics parameters, detects target/outer boundaries and valid-area exits, supports configurable bouncing/resting, and returns an explicit throw outcome. See `docs/STONE_PHYSICS.md` for the Phase 4 contract.
