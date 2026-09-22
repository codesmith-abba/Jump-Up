# Jump-Up Player Movement State Machine

## Phase 5

Phase 5 adds the authoritative, renderer-independent player movement system.

The implementation follows only established Jump-Up rules. The exact physical
traversal path for each layout was explicitly unresolved, so the engine does
**not** infer one from house numbering or geometry.

## Logical state

`MovementState` records:

- `position`: the latest logical point supplied by the caller;
- `current_house_id`: the house containing the player's logical position;
- `direction`: `outbound` or `return`;
- `mode`: `hopping` or `resting`;
- `one_leg`: whether the current landing is one-leg movement;
- `target_house_id`: the house containing the thrown stone;
- `required_outbound_house_ids`: the explicit layout-specific path supplied by the game/layout layer;
- `visited_house_ids`: deterministic movement history.

There is no animation state in this model.

## State machine

```text
THROW_RESOLUTION
      |
      | successful throw
      v
HOPPING_OUT
      |
      | begin_hopping_out(explicit path)
      v
OUTBOUND HOPPING
      |
      | visit required house in supplied sequence
      | skip stone/target house
      v
LAST REQUIRED OUTBOUND HOUSE
      |
      | begin_hopping_back
      v
RETURN HOPPING
      |
      | visit supplied path in reverse
      | then reach target/stones house
      v
TARGET / STONE HOUSE
      |
      | pickup while one-leg + return state
      v
STONE_PICKUP
      |
      v
HOUSE_COMPLETED
```

## Explicit movement path

The repository establishes that the player skips the stone house and traverses
the other required houses, but it does not establish the exact house-to-house
path for every layout.

Therefore Phase 5 requires the authoritative caller to supply an explicit
outbound path. For example, a test can provide:

```text
Target: 2
Outbound path: 1 → 3 → 4
Return: 4 → 3 → 1 → 2
```

That example is test data, not a new universal Jump-Up rule.

The movement validator checks that:

- every path house exists;
- the target/stone house is absent from the outbound path;
- no house is duplicated;
- the submitted hop follows the supplied path exactly.

A later layout-specific phase can define the real paths without rewriting the
movement engine.

## Feet and resting

Normal hopping uses one leg.

Both feet are accepted only when the destination house is owned by the active
player. Such a landing enters `resting` mode. The next valid hop continues the
supplied sequence and returns the movement state to one-leg hopping.

A second foot in an unowned house is a movement violation and causes turn
failure when submitted through the authoritative transition system.

## Boundary validation

A movement destination must be strictly inside its house geometry.

- boundary contact -> failure;
- outside the house -> failure;
- strict interior -> valid landing.

The existing geometry/physics boundary semantics are reused rather than
creating a second boundary implementation.

## Stone retrieval

Retrieval is not a free action. It is legal only when the player is:

- moving in the return direction;
- still in hopping mode;
- using one leg;
- in the target/stone house.

## Failure behavior

A movement violation submitted through `transition()` marks the active turn as
failed and moves it to `TURN_END`, matching the established failure rule.

The player remains in the game.

## Rendering separation

The movement engine does not know about:

- Pygame;
- React Native;
- Expo;
- sprites;
- animation frames;
- touch/gesture events;
- frame rate.

A renderer may animate a legal movement however it chooses, but it cannot make
an illegal movement legal.

## Deliberately unresolved

Phase 5 does not invent:

- exact physical walking/hopping paths between house polygons;
- foot-size/collision radius;
- animation timing;
- gesture interpretation;
- failure persistence beyond the established turn failure;
- new rules for house order or layout geometry.
