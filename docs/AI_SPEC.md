# Jump-Up AI Specification

Phase 11 defines the formal learning boundary:

STATE → ACTION → REWARD → NEXT STATE → DONE

## API

JumpUpAIEnvironment provides reset(seed), observe(), legal_actions(), and step(action).

## State

AIObservation exposes layout identity/type, relevant house geometry, current
player, current/target house, stone state, player position, owned houses,
opponent ownership, scores, round, completed turns, phase, legal actions, and
episode completion. It does not expose transition implementation internals.

## Actions

AIAction has four decision types: THROW, BEGIN_MOVEMENT, HOP, and CLAIM.
The environment computes legal actions from authoritative state. Illegal
actions are rejected before mutation.

## Rewards

Baseline reward: +1 per newly claimed house, -1 for a failed turn, +10 for an
agent win, +2 for an agent tie, -2 for a non-agent tie, -10 for a loss, and
0 otherwise. Rewards are training signals only.

## Determinism and safety

reset(seed) recreates the same episode. Every state mutation passes through
transition(). The environment is not a second rules engine.

## Framework boundary

No Gymnasium, PyTorch, or TensorFlow dependency is required.
