# Jump-Up Game Engine

## Purpose

The game engine is the single authoritative source of Jump-Up game state. Phase 2 established the foundational model and deterministic lifecycle transition boundary. Phase 3 adds renderer-independent house geometry and production layout loading.

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


## Phase 3 — House and Layout System

### Production representation

A Layout is the complete playable arrangement. It has:

- a stable layout ID;
- a LayoutType;
- an ordered tuple of House objects.

Each House has:

- a stable house ID;
- a one-based house number;
- a zero-based sequence index;
- a HouseGeometry value.

HouseGeometry is renderer-independent. It contains:

- a closed boundary outline made of Point(x, y) values;
- an axis-aligned Bounds value;
- derived center, width, and height.

Coordinates are layout-local coordinates derived from the preserved legacy ASCII source. They are not screen pixels and do not depend on Pygame, React Native, SVG, or a device resolution.

House ownership remains dynamic game state in GameState.ownership (house_id -> player_id). It is deliberately not duplicated inside House.

### Legacy ASCII interpretation

The original files are preserved unchanged under Python (Pygame)/houses/.

The prototype's utils.py treats marker-delimited sections as shapes. A production house is not automatically the same thing as one prototype section: a section can contain multiple playable cells.

The Phase 3 loader therefore interprets the existing files as follows:

| Source | Production houses | Interpretation |
| --- | ---: | --- |
| heart.txt | 8 | Each six-row heart section is one playable house. |
| square.txt | 7 | Three vertically stacked single cells, followed by two rows containing two cells each. |
| rect.txt | 6 | The lower 3×2 rectangular grid contains six playable cells. The sloped three-row header is preserved as source geometry/context but is not treated as an independent playable house because it does not form a separate closed cell. |

This interpretation is an explicit production mapping of the existing source data. It does not change the original files.

The legacy loader lives in jumpup.layouts.load_legacy_layout(). It validates the expected source structure and raises LayoutDataError for missing, malformed, or unsupported layout data.

### Geometry and ordering

House geometry is the authoritative static geometry used by future collision/physics, simulation, AI observations, and mobile rendering adapters.

Layout.next_house_id() provides deterministic sequential adjacency for gameplay progression. The layout does not rely on UI coordinates for ordering.

The current geometry layer intentionally does not implement collision or movement rules. Later physics/rule phases will consume the same HouseGeometry values.

### Serialization

GameState.to_dict() now includes each house's boundary, bounds, center, width, and height. This keeps geometry available to deterministic simulation, persistence/replay work, and mobile adapters without exposing renderer-specific objects.

The dictionary remains a Phase 2/3 internal serialization shape, not a versioned public network contract.

### Layout validation tests

Phase 3 tests verify:

- heart house count and stable IDs;
- square splitting into individual playable cells;
- rectangle splitting into individual playable cells;
- house ordering and sequence indexes;
- closed geometry boundaries;
- bounds, centers, and dimensions;
- invalid geometry rejection;
- malformed source rejection;
- unsupported layout rejection.

No mobile board or renderer is implemented in this phase.
