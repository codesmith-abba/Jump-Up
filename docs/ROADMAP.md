# Jump-Up Development Roadmap

## Roadmap Principle

The project will be developed around one invariant:

> **ONE AUTHORITATIVE GAME MODEL**

Every playable surface, AI system, simulator, and automated test must use the same game engine.

## Phase 0 — Formalize the Game Rules
**Status: Complete**
Established the house, layout, player, turn, progression, throw, boundary, hopping, retrieval, completion, claiming, ownership, failure, round, and winning concepts.

Created: docs/GAME_RULES.md and docs/GAMEPLAY_SPEC.md.

Important unresolved rules remain explicitly marked configurable/undefined.

## Phase 1 — Prepare Repository Architecture
**Status: Complete**
Inspected the repository, classified prototype versus production responsibilities, established the authoritative-engine boundary, defined simulation/AI/mobile/test/documentation boundaries, and prevented duplicated rules.

Created: docs/ARCHITECTURE.md and docs/ROADMAP.md.

No complete engine is implemented in this phase.

## Phase 2 — Implement the Authoritative Game State Model
**Status: Implemented; verification pending**
Established the isolated game-engine package, typed authoritative state model, explicit lifecycle phases, action/transition boundary, deterministic state transitions, ownership representation, serialization foundation, and model tests.

The model remains intentionally incomplete for final physics, geometry, round semantics, claim mechanics, and winner calculation.

## Phase 3 — Implement the House and Layout System
**Status: Implemented; verification pending**
Implement Heart, Square, Rectangle, stable house IDs, sequence, renderer-independent geometry, boundaries, dimensions, centers, and legacy-layout loading. Preserve the original ASCII source files and document how individual playable houses are extracted from prototype sections.

**Gate:** no mobile board, physics, or AI implementation is included in this phase.

## Phase 4 — Implement Core Turn/Throw/Movement Rules
**Status: Planned**
Implement player turns, stones, sequential target, throw validation, hopping, boundary failures, stone-house skip, return, retrieval, house completion, and turn failure. Every rule receives direct and scenario tests.

## Phase 5 — Implement Ownership and Claiming
**Status: Planned**
Implement facing selection, back-facing selection, eligible selection, ownership, rejection of already-owned houses, failed claim behavior, owned-house rest, and non-owner movement.

## Phase 6 — Implement Round and Game Completion
**Status: Planned**
Implement round lifecycle, claim availability, end condition, scoring, winner calculation, and tie behavior if defined. Add complete multi-player scenario tests.

## Phase 7 — Headless Simulation
**Status: Planned**
Create a simulation layer consuming the authoritative engine for UI-free games, deterministic replay, scripted sequences, large-scale execution, statistics, and AI evaluation. Do not duplicate rules.

## Phase 8 — AI Foundation
**Status: Planned**
Create the AI boundary with state observation, legal-action interface, action selection, deterministic baseline AI, AI-versus-AI simulation, and tests. First prove AI can play entirely through the engine.

## Phase 9 — AI Training / Advanced Gameplay
**Status: Planned**
Build training environments, generate games, define rewards, benchmark policies, and experiment with search/reinforcement learning or other approaches. Learned policies must still use engine legality.

## Phase 10 — Mobile Engine Integration
**Status: Planned**
Connect React Native to the authoritative game model through an engine adapter, action dispatch, engine-state rendering, and input translation. No duplicated gameplay rules in components.

## Phase 11 — Mobile Gameplay
**Status: Planned**
Build layout rendering, player/stone presentation, throw interaction, hopping, pickup, ownership visuals, turn UI, failure feedback, round UI, winner screen, accessibility, animation, sound, and haptics.

## Phase 12 — Human Multiplayer
**Status: Planned**
Implement local multiplayer for the supported 2–4 player range, including setup, turn rotation, local handoff, persistent game state, and complete local match flow.

## Phase 13 — Production AI Opponents
**Status: Planned**
Integrate production AI opponents with difficulty levels, AI turns, human-versus-AI matches, performance monitoring, and deterministic/debug mode.

## Phase 14 — Full Test and Verification Suite
**Status: Planned**
Expand coverage across engine unit tests, layouts, gameplay scenarios, simulation, AI, mobile integration, and regression fixtures. Add deterministic replay fixtures for important sequences.

## Phase 15 — Production Hardening
**Status: Planned**
Address performance, memory, deterministic replay, error handling, state serialization, crash recovery, device compatibility, accessibility, release configuration, and observability without weakening rule correctness.

## Phase 16 — Release Candidate
**Status: Planned**
Verify complete rules coverage, supported layouts, local multiplayer, AI, completion, mobile UX, automated tests, clean builds, release assets, and documentation.

## Phase 17 — Production Release
**Status: Planned**
Prepare Android/iOS release, store metadata, privacy/legal requirements, crash reporting, analytics where appropriate, and release documentation.

## Phase 18 — Post-Release Evolution
**Status: Planned**
Potential future work includes additional layouts, rule variants, online multiplayer, stronger AI, tournaments, profiles, leaderboards, replay/sharing, and localization. New features must extend the authoritative engine.

## Phase Gates

A phase is complete only when: requirements are implemented; relevant tests exist; existing checks pass; documentation is updated; no duplicate rule implementation exists; unresolved rules remain unresolved unless explicitly decided; existing working functionality is preserved; and the next phase does not begin until the current phase is verified.

## Current Position

Phase 0 — Rules: COMPLETE
Phase 1 — Architecture: COMPLETE
Phase 2 — Authoritative state model: IMPLEMENTED; VERIFICATION PENDING
Phase 3 — House/layout system: IMPLEMENTED; VERIFICATION PENDING
Phase 4 — Core gameplay: PLANNED
Phase 5 — Claiming/ownership: PLANNED
Phase 6 — Rounds/winning: PLANNED
Phase 7 — Simulation: PLANNED
Phase 8 — AI foundation: PLANNED
Phase 9 — AI training: PLANNED
Phase 10 — Mobile integration: PLANNED
Phase 11 — Mobile gameplay: PLANNED
Phase 12 — Local multiplayer: PLANNED
Phase 13 — Production AI: PLANNED
Phase 14 — Full verification: PLANNED
Phase 15 — Hardening: PLANNED
Phase 16 — Release candidate: PLANNED
Phase 17 — Production release: PLANNED
Phase 18 — Post-release: PLANNED