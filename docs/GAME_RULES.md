# Jump-Up Game Rules

## Status

This document formalizes the game rules currently established for the Jump-Up project.

**Important:** Phase 0 is documentation-only. It does not define the implementation architecture or implement the game engine. Where the traditional rules have not yet been established precisely, this document deliberately marks the rule as **configurable/undefined** rather than inventing behavior.

### Rule-status labels

- **Confirmed** — established project/game rule and safe to treat as part of the intended game.
- **Prototype behavior** — behavior or representation observed in the existing Python/Pygame prototype. It is useful evidence, but is not automatically an authoritative gameplay rule.
- **Configurable / undefined** — the project has not established enough detail to make this an implementation rule. A future phase must define it before relying on it.

## 1. Definition of a House

A **house** is one individual playable section of a Jump-Up layout.

A layout is the complete drawing/arrangement placed on the ground. It may contain multiple individual houses.

For example, an eight-heart layout contains eight individual playable houses; those houses are referred to sequentially as House 1 through House 8.

**Confirmed:** A house is not the entire layout.

**Prototype behavior:** The Python prototype stores layout drawings in text files and contains parsing logic intended to extract individual sections from those drawings.

**Configurable / undefined:** The exact authoritative geometric representation and numbering/orientation rules for every future layout have not yet been finalized.

## 2. Layouts

The project currently recognizes three layout styles:

1. **Heart**
2. **Square**
3. **Rectangle**

Current prototype files:
- Python (Pygame)/houses/heart.txt
- Python (Pygame)/houses/square.txt
- Python (Pygame)/houses/rect.txt

**Confirmed:** A layout can contain multiple houses.

**Prototype behavior:** The Python prototype uses marker strings and text-shape parsing to identify sections in the heart and square layouts. The existing rect.txt file contains a rectangular arrangement, but constants.py does not currently define a corresponding Rectangle house type.

**Configurable / undefined:** The final digital geometry, coordinate system, exact house numbering, orientation, dimensions, and boundary representation for each layout remain to be defined by the future authoritative game model.

### Individual house identification

At the rules level, an individual house is identified by its position in the selected layout and its sequential house number.

At the prototype level, individual sections are inferred from the text layout's structural markers.

The prototype parsing approach must not be treated as the final rule for identifying houses. The future game model must represent houses explicitly enough that gameplay, AI, simulation, tests, and rendering all refer to the same house identities.

## 3. Players

**Confirmed:**
- The current digital version supports **2–4 players**.
- Each player has their **own stone**.
- Players take turns.
- A player remains in the game after a failed turn; failure does not eliminate the player.

**Prototype behavior:**
- player.py defines a maximum of four players.
- The prototype contains a player list and add/get/remove methods.
- Turn advancement is not implemented: Player.next_player() is currently pass.

**Configurable / undefined:** player identity representation, starting positions, exact ordering beyond turn progression, and whether future versions support more than four players.

## 4. Turn Flow

The confirmed high-level turn flow is:

1. The current player begins from the current sequential house.
2. The player throws their stone into the target house.
3. The throw is validated.
4. If the throw is invalid, the turn fails.
5. If valid, the player performs the required hopping sequence.
6. The house containing the stone is skipped while moving through the layout.
7. The player returns and picks up their stone while continuing the required movement.
8. If the sequence is completed successfully, the current house is completed.
9. The player may proceed to the next sequential house according to the progression rules.
10. If the player fails at any point, the turn ends and the next player takes their turn.

**Confirmed:** Failure ends the current turn but does not eliminate the player.

**Configurable / undefined:** Exact state transitions and timing of every intermediate action are implementation details for the game-engine phase.

## 5. Sequential House Progression

**Confirmed:** Play begins with the first house; houses are progressed through sequentially; successfully completing the current house permits progression to the next house.

For an eight-house layout: House 1 → House 2 → House 3 → ... → House 8.

A player does not freely choose the next progression house during normal sequential play.

**Configurable / undefined:** Whether progression always starts at House 1 for every player/mode, exact state after reaching the end, interaction between failed claims and progression, and whether variants permit resuming from a different house.

## 6. Stone Throwing

Each player uses their own stone. For a normal turn, the stone is thrown toward the player's current target house.

**Confirmed:** The stone must land within the required target area. A throw that does not satisfy the target-house constraints is invalid and causes turn failure.

**Prototype behavior:** diamond.py contains an experimental projectile model named Diamond with position, velocity, gravity, bouncing, and an active state. utils.py also contains commented-out coordinate checks for whether a thrown object is inside a shape boundary. This is experimental code, not an authoritative rule.

**Configurable / undefined:** physical trajectory versus direct input/aim, throw controls, legal landing tolerance, bouncing, and exact boundary-touch behavior during a throw.

## 7. Valid and Invalid Throws

### Valid throw

A throw is valid when the stone comes to rest in the required target house and satisfies the target-house boundary rules.

### Invalid throw

Confirmed invalid examples include:
- the stone lands outside the required house;
- the stone leaves the required house boundary;
- the stone otherwise fails the required target selection.

An invalid throw causes the current turn to fail.

**Prototype behavior:** Existing prototype code contains bounding-box calculations and commented-out coordinate validation. These demonstrate experimentation with boundary validation but do not define the final collision model.

**Configurable / undefined:** exact handling of corners/vertices, mathematical containment model, and digital tolerance.

## 8. Boundary Behavior

Boundary lines are part of the playable-house rules.

**Confirmed:** the stone must remain within the required house; a stone touching a boundary line is a failure condition; a player stepping on a boundary line is a failure condition.

The boundary therefore has a meaningful distinction from the interior of a house.

**Configurable / undefined:** mathematical boundary definition, precision tolerance, vertex/intersection behavior, and representation for non-rectangular shapes.

## 9. Hopping Rules

**Confirmed:** After a successful throw, the player moves by hopping. Normal movement is performed on **one leg**. The player must follow the required hopping sequence. Putting a second foot down where it is not permitted is a failure.

Confirmed failure conditions include stepping on a boundary line, putting the second foot down where prohibited, and otherwise breaking the required hopping sequence.

**Configurable / undefined:** mobile movement input, animation timing, continuous versus discrete foot positions, and corner transitions.

## 10. Skipping the House Containing the Stone

After a valid throw, the player must **skip the house containing their stone** during the outbound hopping sequence.

Example for House 1: the stone is in House 1; the player does not step into House 1 during the outbound sequence; the player hops through the remaining required houses; the player returns to the stone's house to retrieve it.

**Confirmed:** the stone's house is skipped rather than used as a normal landing house during that part of the sequence.

**Configurable / undefined:** exact path/order through layouts whose geometry is not a simple linear sequence.

## 11. Returning and Picking Up the Stone

After passing through the required houses, the player returns to the house containing the stone.

**Confirmed:** the player retrieves their stone on the return; the player must continue the required movement while retrieving it; retrieval is part of the same successful sequence.

**Configurable / undefined:** hand/foot animation, digital timing, and pickup position/tolerance.

## 12. Completing a House

A house is successfully completed when the player completes the required throw, hopping, skip, return, and stone-retrieval sequence without failing.

**Confirmed:** successful completion allows progression to the next sequential house.

**Configurable / undefined:** whether completed and claimed are always the same state, exact point at which ownership is awarded, and behavior when the current house is already owned by another player.

The distinction between **progressing through a house** and **claiming ownership of a house** must remain explicit in the future engine.

## 13. House Claiming

House claiming is a separate part of the game in which a successfully selected house becomes owned by the player.

**Confirmed:** a successfully selected house becomes owned by the player; a player cannot take or claim a house already owned by another player; house selection can use facing or back-facing mode; a failed house selection does not immediately grant another attempt and waits until the next round.

**Configurable / undefined:** exact relationship between sequential completion and claiming, exact moment in turn/round when claiming occurs, whether every completed house produces a claim attempt, and end-of-game interaction with unclaimed houses.

## 14. Facing Selection Mode

In **facing selection mode**, the player faces the houses and throws their stone toward the house they want to claim.

**Confirmed:** facing selection is a supported mode.

**Configurable / undefined:** exact throw mechanics, legal selection area, whether any eligible house may be selected, and UI/input representation.

## 15. Back-Facing Selection Mode

In **back-facing selection mode**, the player turns their back to the houses and throws without directly facing the layout; the throw determines the selected house.

**Confirmed:** back-facing selection is a supported mode.

**Configurable / undefined:** exact throw mechanics, selection tolerance, boundary resolution, intentional targeting constraints, and UI/input representation.

## 16. Failed Claim Behavior

**Confirmed:** if a house-selection/claim attempt fails, the player does not receive an immediate second attempt; they must wait until the **next round** before attempting to claim a house again.

Failure of a claim is distinct from player elimination.

**Configurable / undefined:** exact definition of a round; whether a failed claim affects sequential progression; and whether progression state is retained after a failed claim.

## 17. Owned Houses

A successfully claimed house becomes owned by the player who claimed it.

**Confirmed:** ownership belongs to a specific player; ownership provides a movement/rest advantage; other players cannot take an already-owned house.

**Configurable / undefined:** whether ownership can ever change, exact visual representation, and any additional persistence rules between rounds.

## 18. Resting in Owned Houses

**Confirmed:** the owner may place both feet inside their own house and rest there. A non-owner must continue normal one-leg hopping when passing through that house.

**Configurable / undefined:** rest duration, whether resting is optional or required, digital foot placement, and additional actions while resting.

## 19. Can Another Player Claim an Already-Owned House?

**Confirmed: No.** A player cannot take or claim a house already owned by another player. Duplicate ownership is not allowed.

## 20. Turn Failure

A turn fails when the player breaks a required throwing or movement rule.

Confirmed examples include invalid/out-of-target throw, stone leaving the required boundary, stone touching a boundary line, player stepping on a boundary line, second foot down where prohibited, and breaking the required hopping sequence.

**Confirmed consequences:** current turn ends; next player takes their turn; player is not eliminated.

**Configurable / undefined:** whether partial progress is preserved after every kind of failure, including failure after house completion but before a claim.

## 21. Round Progression

The project uses the concept of a **round** because a failed claim waits until the next round.

**Confirmed:** a next-round concept exists.

**Configurable / undefined:** round start/end, whether a round is one turn for every player, handling of skipped/failed players, progression across rounds, and claim frequency.

## 22. Winning Condition

**Confirmed:** Jump-Up is a house-claiming competition. The winner is the player who has claimed the **highest number of houses** when the game reaches its ending condition.

**Configurable / undefined:** exact game-ending condition, behavior if no more eligible houses can be claimed, and tie-breaking.

## Confirmed Rule Summary

| Area | Confirmed rule |
| --- | --- |
| House | One individual playable section |
| Layout | May contain multiple houses |
| Layout styles | Heart, Square, Rectangle |
| Players | 2–4 in current digital version |
| Stones | One stone per player |
| Turns | Turn-based |
| Starting progression | Begins at the first/current sequential house |
| Progression | Sequential house progression |
| Throw | Stone must satisfy target-house constraints |
| Hopping | One-leg movement |
| Stone house | Skipped during required outbound movement |
| Retrieval | Player returns and picks up their stone |
| Boundary | Touching/stepping on a boundary is a failure |
| Second foot | Not allowed where prohibited |
| Failure | Ends current turn |
| Elimination | Failure does not eliminate player |
| Claiming | Successful selection gives ownership |
| Claim conflict | Already-owned house cannot be claimed |
| Facing mode | Supported |
| Back-facing mode | Supported |
| Failed claim | Wait until next round |
| Owned house | Owner may use both feet/rest |
| Non-owner | Continues one-leg movement through owned house |
| Winner | Highest number of claimed houses at game end |

## Rules We Must Not Invent Yet

1. Exact round boundaries.
2. Exact claim-attempt timing.
3. Exact relationship between sequential completion and claiming.
4. Exact game-ending condition.
5. Tie-breaking.
6. Exact geometry and coordinate representation for each layout.
7. Exact house numbering/orientation for every layout.
8. Exact digital throw controls and physics.
9. Exact collision tolerances.
10. Exact foot-placement/input model.
11. Exact behavior at corners/intersections.
12. Whether a player retains progression after particular kinds of failure.
13. Whether ownership can ever change.
14. Any additional traditional-game variants not already established by the project.

## Authority Rule for Future Implementation

1. **Formalized rules in this document** define the intended gameplay constraints.
2. **Prototype code** provides historical implementation evidence only.
3. **Prototype artifacts must not silently become rules.**
4. **Undefined rules must remain configurable or blocked from implementation** until explicitly decided.
5. The future game engine should expose explicit state for houses, players, stones, turns, progression, ownership, claims, movement, failures, rounds, and game completion so that the same rules can be used by human play, AI, simulation, automated tests, and the mobile renderer.