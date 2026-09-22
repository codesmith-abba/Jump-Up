# Jump-Up Architecture

## 1. Architecture Goal

Jump-Up must have **ONE AUTHORITATIVE GAME MODEL**.

The rules and state transitions must exist in one authoritative game engine/model. React components, AI, simulation, rendering, and prototype code must consume that model rather than reimplementing gameplay rules.

The architecture separates:
1. **Authoritative game engine** — owns game state, rules, validation, and transitions.
2. **Headless simulation** — runs the engine without UI or rendering.
3. **AI system** — chooses actions through the engine's public action/state interfaces.
4. **Mobile application** — renders engine state and sends player input/actions to the engine.
5. **Tests** — verify the same engine used by every consumer.
6. **Documentation** — defines rules, contracts, architecture, and decisions.

Phase 1 establishes this architecture but does not implement the complete engine.

## 2. Current Repository Assessment

The repository currently has: Python (Pygame), Mobile App (React Native), docs, and README.md.

### Python/Pygame

The Python side is a historical prototype.

Observed files include jumpup.py, player.py, diamond.py, utils.py, constants.py, character.py, runner.py, modal.py, color_generator.py, houses/*.txt, and static/.

Important observations: jumpup.py contains UI/state-selection code but not a complete authoritative gameplay loop; player.py has player collection helpers but next_player() is unimplemented; utils.py contains layout parsing and experimental state helpers while transition_model, check_winner, and winner are unimplemented; WON_HOUSES = [1, 4, 2] is prototype data, not a rule; diamond.py contains experimental projectile physics; constants.py has Heart and Square types/markers but no Rectangle type although rect.txt exists.

No Python dependency manifest such as requirements.txt, pyproject.toml, or setup.py was found at the inspected prototype root, and no Python test suite was found there.

**Decision:** Do not evolve the prototype into the authoritative engine by adding more gameplay into these files. Keep it as historical/reference material.

### House layouts

Current prototype representations are heart.txt, square.txt, and rect.txt under Python (Pygame)/houses/.

These are useful source assets/reference data, but their text-marker representation is not sufficient by itself to define the production domain model.

The future engine should consume explicit layout definitions with stable house identities, geometry/boundaries, and traversal relationships.

The original files should remain unchanged until a dedicated layout-migration phase decides how to convert them.

### React Native / Expo

The mobile application is currently an Expo starter application.

Observed dependencies include Expo ~53.0.20, React 19.0.0, React Native 0.79.5, TypeScript ~5.8.3, Expo Router ~5.1.4, ESLint/eslint-config-expo, Reanimated, Gesture Handler, navigation, image/font utilities, and related Expo packages.

The app currently contains starter Home/Explore screens, Expo routing, reusable starter components, hooks, constants, assets, and package metadata.

**Decision:** The mobile application remains the presentation/input layer. Game rules must not be added to screen components.

### Assets

The mobile app contains Expo starter assets under assets/images and assets/fonts. The Python prototype contains static assets under Python (Pygame)/static/.

These assets can be reused selectively, but asset reuse does not imply code or prototype behavior reuse.

## 3. Proposed Production Structure

The repository should evolve toward:

Jump-Up/
docs/
  ARCHITECTURE.md
  GAME_RULES.md
  GAMEPLAY_SPEC.md
  ROADMAP.md
game-engine/
  src/jumpup/
    domain/
    rules/
    layouts/
    engine/
  tests/
simulation/
  src/
  tests/
ai/
  src/
  tests/
Mobile App (React Native)/
  jump-up/
Python (Pygame)/
  historical prototype/reference

This is a target architecture, not a request to create all directories immediately.

### Why a separate engine location?

The existing Python prototype mixes rendering, UI state, experimental physics, layout parsing, and incomplete game-state helpers. That makes it unsuitable as the long-term authoritative boundary.

A dedicated game-engine package provides a clean dependency direction and a headless reusable core.

## 4. Authoritative Game Engine

The engine is the core of the project.

It should eventually own the domain model: Game, Player, Stone, Layout, House, Ownership, Turn, Round, Claim attempt, Movement state, Failure/result, and Game completion.

It should own the rules for house sequencing, valid target throws, boundary validation, hopping, stone-house skipping, return/retrieval, house completion, claim selection, facing/back-facing selection, ownership restrictions, owned-house resting, turn failure, round progression, and scoring/winner calculation.

The engine should receive a domain action, validate it against current state and established rules, and produce the next authoritative state/result.

The engine should be deterministic for the same initial state, configuration, and action sequence. Any future randomness should be injected explicitly.

## 5. Engine Boundary

Consumers should interact through a stable engine-facing interface rather than reaching into internal implementation details.

Conceptually: GameState + GameAction → GameEngine → TransitionResult + New GameState.

The exact Python classes/types will be defined during engine implementation.

Human input, AI, simulation, and tests must all submit actions to the same engine.

## 6. Headless Simulation

The simulation layer runs games without a UI.

It should create configured games, execute engine actions, run many games, collect outcomes/statistics, reproduce deterministic scenarios, and support future AI training/evaluation.

Simulation must call the same engine used by the mobile app and must not create a second simplified rules engine.

Allowed dependency: simulation → game-engine. The reverse dependency is forbidden.

## 7. AI System

AI is a consumer of the authoritative engine.

AI should inspect an engine-provided state/observation, choose a legal action according to its policy, submit that action through the engine, receive the resulting state, and repeat.

AI must not directly mutate game state and must not independently implement boundary, hopping, ownership, turn, or winning rules.

Future policies can include deterministic/basic AI, heuristic AI, search/planning, simulation-trained AI, or learned models. These are policy choices, not rule implementations.

## 8. Mobile Application

### UI owns

Rendering, navigation, animation, touch/gesture capture, sound/haptics, presentation, accessibility, and device integration.

### Engine owns

Legality, game state, progression, collision/rule decisions, ownership, turn changes, and game completion.

React components must not independently decide whether a throw is valid, who owns a house, which house a player should target, or who wins. They send actions to the engine and render the returned state/result.

## 9. Rendering and Geometry Boundary

The engine needs authoritative gameplay geometry but must not depend on React Native rendering primitives.

Layout/domain data should describe geometry in renderer-independent terms: stable house ID, sequence/index, playable geometry, boundary geometry, traversal relationships, and ownership state.

The mobile renderer may transform this into SVG, Canvas, React Native Views, animation coordinates, or other rendering primitives.

The engine must not know about JSX, View, StyleSheet, SVG components, or screen pixels.

## 10. Prototype Boundary

The Python/Pygame prototype remains valuable for original gameplay ideas, historical behavior, visual references, layout source material, experimental movement/throw concepts, and identifying unfinished areas.

It is not authoritative.

Prototype code that should remain prototype-only unless explicitly extracted and verified includes jumpup.py, runner.py, diamond.py, player.py, incomplete functions in utils.py, prototype marker parsing, hard-coded WON_HOUSES, and experimental animation code.

Potentially reusable assets/data include house layout source files, visual assets, character references, and colors. Reuse requires validation against the formal rules and production representation.

No prototype code should be deleted merely because the new architecture exists.

## 11. Layout Migration Strategy

Do not immediately rewrite the existing .txt layouts.

First preserve the source files; define the production layout schema; decide exact geometry/path/numbering rules; create explicit production layout definitions; write layout tests; compare production layouts against reference files; then decide whether text files remain source assets or are retired.

## 12. Testing Architecture

Tests should exist at several levels.

### Engine unit tests

Test domain objects, action validation, transitions, boundaries, house sequencing, ownership, and failure behavior.

### Engine scenario tests

Test complete sequences such as valid throw → hop → skip → return → retrieve → complete → progress, plus failure scenarios.

### Layout tests

Verify house count, identity, ordering, geometry, boundaries, and traversal relationships.

### Simulation tests

Verify that simulation uses the real engine and produces reproducible results.

### AI tests

Verify legal-action selection, policy behavior, no direct state mutation, and engine compatibility.

### Mobile tests

Verify rendering, input translation, screen/navigation behavior, and correct display of engine state. Gameplay-rule tests should remain primarily in the engine test suite.

## 13. Dependency Direction

Intended dependency direction:

game-engine → no UI/AI dependency
simulation → game-engine
AI → game-engine
mobile gameplay integration → game-engine
React Native components → engine adapter/state, never a second rules engine
Pygame prototype → no production dependency

## 14. Package/Technology Decision

The current repository does not contain a production Python package or Python dependency manifest for the prototype.

The engine should therefore be introduced as a new isolated Python package rather than turning Python (Pygame) into the engine.

This preserves the historical prototype while creating a testable, headless, reusable core.

The precise packaging/build tooling should be established in the engine-foundation phase.

## 15. Reuse Policy

### Reuse directly

Only if a prototype component is self-contained, correct under the formal rules, free of UI coupling, and verified by tests.

### Extract/adapt

When the underlying concept is useful but implementation is prototype-specific, such as layout source data or visual constants.

### Keep prototype-only

If incomplete, experimental, UI-coupled, or contradictory to the formal specification, such as incomplete state functions, Diamond physics, WON_HOUSES, and the Pygame event/game loop.

### Retire later

Only after the production replacement is verified and the prototype is no longer needed.

## 16. Architecture Invariants

1. **One authoritative game model.**
2. UI never owns game rules.
3. AI never owns game rules.
4. Simulation never owns game rules.
5. Prototype code never becomes authoritative by accident.
6. Engine state is explicit and testable.
7. Engine logic is headless.
8. Engine does not depend on React Native/Pygame.
9. Mobile renders engine state rather than reconstructing it.
10. The same engine drives human play, AI, simulation, and automated gameplay tests.
11. Undefined rules from GAME_RULES.md must not be silently invented in code.
12. New dependencies must be justified and kept minimal.

## 17. Phase 1 Boundary

Phase 1 establishes architecture and repository boundaries. It does not implement the complete game engine, final layouts, physics, mobile gameplay, AI, simulation, or multiplayer networking.