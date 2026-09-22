# Jump-Up Stone Physics

## Phase 4

The authoritative engine contains a deterministic, renderer-independent stone
throw simulator in `jumpup.physics`.

### Prototype reference

The original `Python (Pygame)/diamond.py` was inspected first. It has position,
velocity, gravity, bounce factor, radius, and an active flag. It is experimental
prototype code, so Phase 4 does not port it directly.

### Model

The simulator uses:

- x/y = board coordinates from authoritative `HouseGeometry`;
- z = stone height above the board;
- vx/vy/vz = velocity;
- gravity acting on z;
- z=0 as the board plane.

A fixed timestep makes results independent of renderer frame rate and wall-clock
timing. The same initial state and configuration produce the same result.

### Configurable parameters

`PhysicsConfig` exposes gravity, restitution, horizontal damping, timestep,
maximum time, maximum bounces, resting threshold, and boundary tolerance.
These values are engineering defaults, not claims about historically exact
Jump-Up physics.

### Collision semantics

At board contact:

1. outside the valid area -> failed out-of-bounds;
2. target or outer boundary touched -> failed boundary;
3. strict target interior -> successful landing;
4. elsewhere inside the valid area -> bounce until resting/bounce limit.

Boundary contact is never treated as target interior.

### Separation

The physics module contains no Pygame, React Native, Expo, rendering, animation,
or UI dependencies. Mobile integration is intentionally deferred.

### Phase 4 non-goals

No turn-state integration, player movement, AI, simulation service, multiplayer,
or React Native changes are made in this phase.
