# Jump-Up Game Engine

## Purpose

The game engine is the single authoritative source of Jump-Up game state. Phase 2 established the foundational model and deterministic lifecycle transition boundary. Phase 3 adds renderer-independent house geometry and production layout loading. Phase 4 adds deterministic stone physics. Phase 5 adds authoritative logical player movement and hopping validation. Phase 6 adds authoritative house ownership and claiming.

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
- ClaimState: selected house/player, facing mode, actual claim-throw result, and failure data.
- WinnerState: final winner/tie information.
- GamePhase: explicit lifecycle phase.
- Configurable claim retry timing.

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

A failed throw or movement violation moves to TURN_END. A failed claim throw also moves to TURN_END. A completed turn moves through NEXT_PLAYER before another turn begins.

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
- explicit layout-specific outbound movement path;
- visited houses during the current movement sequence.

The movement implementation contains no rendering or animation concerns.

### Outbound movement

After a successful throw, `begin_hopping_out(movement_path)` initializes one-leg hopping. The path is supplied explicitly because the exact layout-specific traversal path was not established by the project specification.

The validator requires that the supplied outbound path:

- contains only houses in the selected layout;
- does not contain the target/stone house;
- contains no duplicate houses;
- is followed exactly by subsequent hops.

The engine therefore enforces the established stone-house skip without inventing a universal physical traversal path.

### Return movement

After all supplied outbound houses have been visited, `begin_hopping_back()` switches direction. The return path is the supplied outbound path in reverse, followed by the target/stone house.

Stone retrieval is legal only after the player reaches the target house during this return movement, while still in one-leg hopping state.

### Foot rules

Normal movement uses one leg.

A two-foot landing/rest is accepted only when the destination house is owned by the active player. An attempt to use both feet in an unowned house is a movement violation and fails the turn.

After resting in an owned house, a subsequent valid hop continues the supplied movement path and returns the movement state to one-leg hopping.

### Boundary rules

A destination position must be strictly inside the destination house geometry. Boundary contact is rejected, and a position outside the destination house is rejected.

The existing renderer-independent geometry and Phase 4 boundary helpers are reused; no second boundary implementation was introduced.

### Movement failure

The transition layer records the validation error in `TurnState.failure_reason`, sets `TurnState.failed`, and moves the game to `TURN_END`. The player remains in the game, matching the established failure rule.

### Rendering separation

The movement layer does not know about Pygame, React Native, Expo, sprites, animation frames, gestures, or frame rate. A renderer can animate a legal movement, but it cannot change the authoritative legality result.

For the full movement state machine, see `docs/MOVEMENT_STATE_MACHINE.md`.

## Phase 6 — House ownership and claiming

A house has exactly one authoritative ownership state:

- unclaimed: the house ID is absent from `GameState.ownership`;
- owned: the house ID maps to exactly one player ID.

Ownership is persistent game state. A successful claim adds the selected house to `ownership`; no later turn automatically removes it.

### Claim selection

Claim selection is available after the current player completes a house.

The selected house must be the house completed by that turn. The engine does not allow arbitrary selection of another house.

Two explicit selection modes are supported:

- `ClaimSelectionMode.FACING` (`facing`)
- `ClaimSelectionMode.BACK_FACING` (`back_facing`)

Invalid modes are rejected. An already-owned house cannot be selected.

### Actual claim throw

Selection and ownership are separate steps:

```text
CLAIM_SELECTION
      |
      | choose house + facing mode
      v
CLAIM_RESOLUTION
      |
      | resolve actual claim throw outcome
      +---- success ----> ownership awarded
      |
      +---- failure ----> no ownership
```

`GameAction.resolve_claim(success, failure_reason)` records the deterministic result of the player's actual claim throw. A physics layer can derive `success` and `failure_reason` from its `ThrowResult`; the authoritative game model does not duplicate the physics implementation.

Therefore a selected house is **not owned merely because it was selected**. Ownership is awarded only after successful claim-throw resolution.

### Claim failure

A failed claim:

- never adds ownership;
- never increments the player's score;
- records the failure reason;
- moves the turn to `TURN_END`;
- optionally prevents another claim attempt by that player until a configurable round.

`GameConfig.claim_retry_rounds` controls the retry timing. The default is `1`, meaning a failed claim at round `N` cannot be attempted again until round `N + 1`. A value of `0` allows retry in the current round.

The exact round timing therefore remains configurable rather than being presented as an unsupported historical certainty.

### Scoring

Score is derived directly from ownership:

```text
player score = number of houses owned by that player
```

`GameState.scores` returns all player scores, and `GameState.score_for(player_id)` returns one player's score.

There is no separate mutable score counter that could diverge from ownership.

### Resting privilege

Phase 5 movement already enforces the ownership privilege: a player may use both feet/rest only in a house owned by that player. Phase 6 ownership therefore automatically affects movement legality through the authoritative `ownership` map.

### Claiming and AI

No AI strategy, prediction, target selection strategy, or automated claim decision is implemented in Phase 6. The engine only evaluates explicit player actions and actual throw outcomes.

## Phase 4 — Deterministic stone physics

Phase 4 adds `jumpup.physics`, a renderer-independent deterministic stone throw simulator. It consumes the authoritative `HouseGeometry` and `Bounds` types, uses a fixed timestep, exposes configurable physics parameters, detects target/outer boundaries and valid-area exits, supports configurable bouncing/resting, and returns an explicit throw outcome. See `docs/STONE_PHYSICS.md` for the Phase 4 contract.
