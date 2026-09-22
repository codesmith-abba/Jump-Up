# Jump-Up Game Engine

## Purpose

The game engine is the single authoritative source of Jump-Up game state. Phase 2 establishes the foundational model and deterministic lifecycle transition boundary.

It is intentionally independent of React Native, Expo, Pygame, AI, networking, and rendering.

## Phase 2 model

The authoritative snapshot is GameState. It contains:

- Layout: stable layout identity, layout type, and ordered houses.
- House: stable ID, sequential number, and sequence index.
- Player: stable ID, name, stone reference, and turn order.
- Stone: stable ID, owner, current house location, and hand state.
- TurnState: current player, current/target house, stone, completion and failure data.
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

A failed throw moves to TURN_END. A failed claim also moves to TURN_END. A completed turn moves through NEXT_PLAYER before another turn begins.

GAME_OVER is an explicit terminal phase with WinnerState.

This is a state-model foundation. Later phases define the exact traditional-game rules that determine when each transition is legal and how movement, claiming, rounds, and game completion work.

## Transition API

Consumers submit one explicit GameAction to:

transition(GameState, GameAction) -> TransitionResult

The transition function:

1. checks the current phase;
2. validates action data;
3. creates a new GameState;
4. leaves the input state unchanged;
5. returns the new state and the applied action.

Invalid actions raise InvalidTransitionError.

There is no UI event handling in this layer.

## Authoritative ownership

Ownership is represented centrally as:

house_id -> player_id

A house cannot be selected for a claim when it is already owned. Successful claim resolution records the owner in the authoritative GameState.

Claim selection stores the selection mode as data rather than embedding facing/back-facing behavior into UI code. The exact mechanics of those modes remain a later rules phase.

## Serialization

GameState.to_dict() returns JSON-compatible primitives.

This is suitable as a foundation for:

- persistence;
- deterministic replay;
- simulation;
- API transport;
- mobile state adapters.

The Phase 2 dictionary format is not yet a versioned network/storage contract.

## Determinism

For the same GameState and GameAction, transition() produces the same resulting state.

The foundational model has no:

- random number generation;
- clocks;
- network calls;
- rendering state;
- hidden global state.

Future randomness must be represented explicitly and injected at a higher-level boundary.

## Validation

The model validates:

- unique player IDs;
- unique stone IDs;
- valid player-to-stone references;
- configured player limits;
- valid house numbering and sequence indexes;
- ownership references;
- turn references;
- current-player references;
- valid lifecycle phase for each action;
- target-house correctness for throws;
- ownership restrictions for claims;
- required claim data before claim resolution.

## What is not implemented in Phase 2

Phase 2 does not implement:

- final house geometry;
- boundary collision mathematics;
- throw physics;
- hop paths;
- foot placement validation;
- stone trajectory simulation;
- exact facing/back-facing selection mechanics;
- final claim timing rules;
- round-ending rules;
- final winner calculation;
- mobile UI;
- AI;
- networking.

Those concerns remain outside this model until their dedicated phases.

## Tests

The Phase 2 test suite covers:

- initial state;
- player creation;
- stone ownership;
- turn initialization;
- explicit lifecycle transitions;
- successful and failed claims;
- failed throws;
- house progression;
- deterministic player/game progression;
- ownership restrictions;
- invalid transitions;
- invalid model references;
- player limits;
- JSON serialization;
- non-mutation of the previous state.

The tests live under game-engine/tests and use the same transition function that future consumers will use.
