# Jump-Up Gameplay Specification

## 1. Purpose

This document converts the currently established Jump-Up rules into an implementation-oriented specification without implementing the game engine.

The specification is intentionally conservative. It defines what the project currently knows, identifies prototype-only behavior, and isolates unresolved decisions so later implementation does not accidentally turn guesses into game rules.

## 2. Scope

This specification covers layouts and houses; players and stones; turns; sequential progression; throws; hopping; skipping and retrieval; house completion; house claiming; facing/back-facing selection; ownership; rest; failures; rounds; and winning.

It does not define the React Native UI, animation implementation, network multiplayer, persistence, AI strategy, physics implementation, or the final engine API.

## 3. Core Domain Concepts

### 3.1 Game

A game contains one selected layout, a finite ordered set of houses, 2–4 players, one stone per player, the current turn, player progression state, house ownership state, claim-selection mode, round state, and game completion state.

The exact data structures are intentionally deferred to the game-engine phase.

### 3.2 Layout

A layout is the complete playable arrangement. Current named layout types are heart, square, and rectangle. A layout contains one or more houses.

### 3.3 House

A house is one individual playable section within a layout.

Each house should have a stable identity within a game, conceptually consisting of layout, house number/index, geometry/boundary, and ownership state. The exact API/schema is not defined in Phase 0.

### 3.4 Player

A player is a participant in the game. Each player has a unique identity, exactly one stone, a sequential progression state, an ownership set, and a current-turn state when active.

### 3.5 Stone

Each player has their own stone. The stone participates in target-house throws, temporary placement, skipping of its house, retrieval, and claim selection where the selected mode uses a throw.

The existing Python Diamond class is not authoritative for the stone domain model.

## 4. Layout and House Model

### 4.1 House numbering

Houses are sequentially identified. For an eight-house layout: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8.

The exact geometric path corresponding to those numbers must be explicitly defined by each layout definition.

### 4.2 House boundaries

Every playable house has a boundary. Gameplay distinguishes inside the house, boundary line, and outside the house. A boundary touch is not treated as a valid interior position.

### 4.3 Prototype representation

The Python prototype represents layouts as text files containing # characters and uses marker-based parsing.

Relevant files: Python (Pygame)/houses/heart.txt, Python (Pygame)/houses/square.txt, Python (Pygame)/houses/rect.txt. utils.py contains extract_each_shape() and get_shape_boundary(). constants.py defines heart and square parsing markers, but currently has no Rectangle house type.

This is implementation evidence only. The future engine should not depend on text-marker parsing as the gameplay authority unless a later architecture decision explicitly chooses it.

## 5. Player and Turn Model

### 5.1 Player count

Current digital scope: minimum 2, maximum 4.

### 5.2 Turn ownership

Exactly one player is the active player for a turn. The turn sequence is cyclic over participating players.

The existing prototype has not implemented the transition function: Player.next_player() is currently pass.

### 5.3 Failure transition

A failed active turn transitions control to the next player. Failure does not remove the player from the game.

## 6. Normal Sequential Gameplay

The established sequence is:

Current player → Current target house → Throw stone → Validate throw → invalid: turn failure → next player; valid: one-leg hopping → skip stone house → traverse required houses → return → pick up stone → complete current house → advance to next sequential house.

This describes the established gameplay concept. Exact event granularity belongs to the future engine.

## 7. Throw Validation

A normal target throw must satisfy the target-house rules.

### Valid

The stone is within the required target house and does not violate the applicable boundary rule.

### Invalid

At minimum: stone outside the required house; stone leaving the required boundary; stone touching a boundary line where the boundary rule applies.

An invalid throw causes turn failure.

### Not yet defined

Exact trajectory, stopping condition, corner/vertex handling, coordinate tolerance, input gesture, and physics simulation.

## 8. Movement Validation

The player moves by hopping. Normal hopping uses one leg.

The active player must not step on a boundary line, place a second foot down where prohibited, or otherwise break the required hopping sequence. A movement violation causes turn failure.

The exact digital movement model remains undefined.

## 9. Stone-House Skip

For current target house H: stone → H; player skips H during required outbound movement; player traverses remaining required houses; player returns to H; player retrieves stone.

The exact traversal path is layout-specific and must be represented explicitly later.

## 10. Stone Retrieval

The stone must be retrieved during the return portion of a successful sequence.

Retrieval is not a separate free action that bypasses movement rules. The player must remain within the required movement constraints while retrieving the stone.

The exact interaction/timing is undefined.

## 11. House Completion

A target house is completed only after the required sequence is successfully finished.

Minimum successful sequence: valid target throw; required hopping; correct stone-house skip; required traversal; return; stone retrieval; no rule violation.

Successful completion permits progression to the next sequential house.

## 12. Claim Selection

Claiming is modeled separately from ordinary sequential movement. A claim attempt selects a house that may become owned.

### 12.1 Facing mode

The player faces the layout and throws toward the desired selection.

### 12.2 Back-facing mode

The player faces away from the layout and throws to determine the selected house.

### 12.3 Selection result

A successful selection results in ownership of the selected eligible house. A house already owned by another player is not eligible.

### 12.4 Failed selection

A failed claim does not produce an immediate retry. The player waits until the next round for another claim attempt.

## 13. Ownership State

A house can conceptually be unowned or owned by one specific player. Only one player can own a house at a time.

Once owned, the house cannot be claimed by another player under the confirmed rules.

Whether ownership can ever be released or transferred is not defined; no implementation should invent such a transition.

## 14. Owned-House Movement

If the active player owns a house, they may place both feet inside it and rest there.

If another player owns it, the active player does not receive that ownership privilege and must continue normal one-leg movement.

The exact digital meaning of rest is undefined beyond the confirmed permission to use both feet and rest.

## 15. Failure Model

A turn failure has the established consequence: current turn → FAILURE → turn ends → next player.

Examples include invalid throw, stone outside target, stone touching boundary, player touching/stepping on boundary, second foot down where prohibited, and broken hop sequence.

Failure does not eliminate the player.

### Unresolved failure persistence

The project has not established whether every form of partial progress is preserved after every failure. Therefore the engine specification must not assume a persistence rule that has not been decided.

## 16. Round Model

The concept of a round exists because a failed claim waits until the next round.

A complete round definition has not yet been established.

The future implementation must define round start, round end, players included, turn count per round, interaction with failed turns, interaction with house progression, and claim availability per round.

Until then, round is a domain concept but not a fully specified transition algorithm.

## 17. Game Completion and Winner

The established scoring rule is: score(player) = number of houses owned by player.

The winner is the player with the highest score when the game reaches its ending condition.

Unresolved: exact ending condition, tie handling, whether all houses must be claimed, whether an end-of-layout event ends the game, and whether there is a round limit.

## 18. State Requirements for the Future Engine

The future authoritative engine will need to represent, at minimum:

### Game configuration
- selected layout;
- player count;
- claim selection mode.

### Static layout state
- ordered houses;
- house geometry;
- house boundaries;
- house adjacency/path information as required by the layout.

### Dynamic game state
- active player;
- current round;
- each player's current sequential target;
- each player's stone state/location;
- house ownership;
- current turn phase;
- current claim attempt, if any;
- failure state/event;
- game completion state.

The exact class/type names are intentionally not specified here.

## 19. Required Validation Boundaries

| Validation | Required result |
| --- | --- |
| Target throw inside eligible house | valid |
| Target throw outside required house | failure |
| Stone touches prohibited boundary | failure |
| Player steps on boundary | failure |
| Player puts second foot down where prohibited | failure |
| Player skips stone house | required |
| Player retrieves stone on return | required |
| Successful sequence | house completed |
| Claim of unowned eligible house | ownership awarded |
| Claim of already-owned house | rejected |
| Failed claim | no immediate retry |
| Owner in owned house | both feet/rest permitted |
| Non-owner in another player's house | normal one-leg rule |
| Turn failure | next player |
| Failure | player remains in game |
| Winner | highest number of owned houses at game end |

## 20. Prototype Evidence Register

### jumpup.py

Observed: layout files are loaded from houses/; available modes include Single Player (With AI) and Multiplayer; player-count choices are 2, 3, and 4; UI/game-state flow includes welcome, house selection, and mode selection; no complete gameplay loop is implemented; ai_active and ai_turn fields exist, but no complete AI gameplay exists.

### player.py

Observed: maximum player count is 4; players can be added, listed, and removed; next_player() is not implemented.

### diamond.py

Observed: experimental projectile object with velocity/gravity/bounce calculations and standalone executable example. This does not establish final stone physics.

### utils.py

Observed: layout loading; marker-based shape extraction; bounding-box calculation; a hard-coded WON_HOUSES = [1, 4, 2] prototype value; unimplemented get_players(), transition_model(), check_winner(), and winner(). The hard-coded WON_HOUSES value is not a game rule.

### constants.py

Observed: HEART and SQUARE house types; heart/square parsing markers; no rectangle enum despite rect.txt existing. This is a prototype inconsistency, not a rule that Rectangle is unsupported.

### React Native / Expo application

Observed: Expo/React Native project is present; routing and tab structure are standard starter structure; current Home and Explore screens are starter content; no authoritative Jump-Up gameplay engine exists in the mobile application yet.

The mobile app is therefore a target platform, not a current source of gameplay rules.

## 21. Implementation Readiness Gate

Phase 0 is implementation-ready for **only the rules marked Confirmed**.

Before implementing a corresponding engine behavior, the project should have an explicit decision for every currently undefined rule that affects that behavior.

In particular, the next gameplay-engine work must not silently decide: round semantics; claim timing; end condition; tie handling; exact layout geometry/path; throw physics/input; collision tolerance; unresolved progression-after-failure behavior.

This prevents the engine from becoming the accidental source of game rules.

## 22. Phase 0 Non-Goals

This phase does not create a game engine, modify Python gameplay code, modify React Native gameplay code, port Pygame logic to React Native, implement AI, implement physics, implement multiplayer, choose unresolved rules, or replace the prototype.

Phase 0 establishes the written contract that later implementation phases can build against.