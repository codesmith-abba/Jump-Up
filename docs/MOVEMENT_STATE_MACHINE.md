# Jump-Up Player Movement State Machine

## Phase 5

Phase 5 adds the authoritative, renderer-independent player movement system.

The implementation deliberately follows only rules already established in
`docs/GAMEPLAY_SPEC.md`. It does not define a physical path between houses,
foot animation, gesture timing, or any other unresolved digital movement rule.

## Logical state

`MovementState` records:

- `position`: the latest logical point supplied by the caller;
- `current_house_id`: the house containing the player's logical position;
- `direction`: `outbound` or `return`;
- `mode`: `hopping` or `resting`;
- `one_leg`: whether the current landing is one-leg movement;
- `target_house_id`: the house containing the thrown stone;
- `visited_house_ids`: deterministic movement history for the current sequence.

There is no animation state in this model.

## State machine

```text
THROW_RESOLUTION
      |
      | successful throw
      v
HOPPING_OUT
      |
      | begin_hopping_out
      v
OUTBOUND HOPPING
      |
      | visit required house in sequence
      | skip target/stones house
      v
LAST REQUIRED OUTBOUND HOUSE
      |
      | begin_hopping_back
      v
RETURN HOPPING
      |
      | visit required houses in reverse sequence
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

## Outbound rule

For target house `H`, the logical outbound sequence is every layout house in
its established sequential order except `H`.

Example for houses `1 → 2 → 3 → 4` and target `2`:

```text
Outbound: 1 → 3 → 4
Return:   4 → 3 → 1 → 2
```

The target house is therefore never accepted as an outbound landing.

## Return rule

Return traversal reverses the required outbound sequence and then ends at the
stone house. Retrieval is legal only when:

- direction is `return`;
- movement is still hopping;
- one leg is being used;
- current house is the target/stone house.

Pickup cannot bypass the movement sequence.

## Feet and resting

Normal hopping uses one foot.

Both feet are accepted only when the destination house is owned by the active
player. Such a landing enters `resting` mode. The next valid hop continues the
required sequence and returns the movement state to one-leg hopping.

A second foot in an unowned house is a movement violation and causes turn
failure when submitted through the authoritative transition system.

## Boundary validation

A movement destination must be strictly inside its house geometry.

- boundary contact -> failure;
- outside the house -> failure;
- strict interior -> valid landing.

The existing geometry/physics boundary semantics are reused rather than
creating a second boundary implementation.

## Failure behavior

A movement violation submitted through `transition()` marks the active turn as
failed and moves it to `TURN_END`, matching the established failure rule.

The player remains in the game and the next-player flow remains responsible for
continuing play.

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

Those require explicit game-rule decisions or later layout-specific work.
