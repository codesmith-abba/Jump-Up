# Jump-Up

Jump-Up is a digital adaptation of a traditional Nigerian children's game played especially among girls. The game combines **stone throwing, one-leg hopping, house claiming, and turn-based competition**.

The project contains an original **Python/Pygame prototype** and a **React Native/Expo mobile application** that is being developed as the target mobile version.

## About the Game

Players create a series of connected **houses** (playable sections) and each player has their own small stone. A player takes a turn by throwing their stone into the current house and then hopping through the remaining houses while following the rules of the game.

In Jump-Up, a "house" means **one individual playable section**, not the entire drawing/layout. For example, if a heart layout contains eight heart-shaped sections, those are eight separate houses: House 1 through House 8.

## How the Game Works

### Players

- The game supports **2 or more players**.
- The current digital version is limited to **2–4 players**.
- Each player has their own stone.
- Players take turns.

### Starting a Turn

The player begins with the first house.

1. The player throws their stone into the current house.
2. The throw must remain within the boundaries of the target house.
3. After a successful throw, the player raises one leg and begins hopping.
4. The player skips the house containing their stone and hops through the other houses.
5. When returning, the player picks up their stone while continuing the required movement.
6. Successfully completing the sequence completes that house and the player can continue to the next house.

For example, when playing House 1 on an eight-house layout:

```text
Throw stone → House 1

Hop:  House 2 → House 3 → House 4 → House 5
       → House 6 → House 7 → House 8

Return → pick up stone from House 1
         → continue hopping

House 1 completed → continue to House 2
```

The player continues progressing from house to house **until they fail**. Once they fail, their turn ends and the next player continues.

## Claiming Houses

Successfully progressing through the game allows a player to claim a house.

The method used to select a house depends on the rules selected at the beginning of the game.

### Facing Selection

The player faces the houses and throws their stone toward the house they want to claim.

### Back-Facing Selection

The player turns their back to the houses and throws without directly facing the layout, selecting a house through the throw.

A successfully selected house becomes **owned by that player**.

Players cannot take or claim a house that is already owned by another player.

### Failed House Selection

If the stone leaves the boundary or otherwise fails the required selection, the player does not immediately get another attempt. They must wait until the **next round** before attempting to claim a house again.

## Owned Houses

A claimed house gives the owner a special advantage during movement.

When the owner reaches their own house, they are allowed to:

- Put **both feet** inside the house.
- Rest normally in that house.
- Continue the game afterward.

A player who does not own a house must continue following the normal one-leg hopping rules when passing through it.

## Failure Conditions

A player's turn ends when they break one of the movement or throwing rules.

Examples include:

- The stone lands outside the required house.
- The stone leaves the house boundary.
- The stone touches a boundary line.
- The player steps on a boundary line.
- The player puts their second foot down where the rules do not permit it.
- The player otherwise fails the required hopping sequence.

When a player fails, the current turn stops and the **next player takes their turn**.

Failure does not eliminate the player from the game. They continue participating when their next turn comes around.

## Winning

Jump-Up is a house-claiming competition.

The winner is the player who has **claimed the highest number of houses** when the game reaches its ending condition.

The game is therefore not simply about being the first player to finish the layout. Players compete to successfully complete their turns and claim as many houses as possible.

## House Layouts

The original prototype supports multiple layout styles, including:

- **Heart**
- **Square**
- **Rectangle**

The layouts are data-driven in the Python prototype. Individual sections are parsed as separate playable houses, allowing the game to reason about their boundaries and positions.

## Game Modes

The project is designed around two primary modes:

- **Single Player with AI** — the player competes against computer-controlled opponents.
- **Multiplayer** — multiple players take turns on the same game.

The prototype supports player counts of **2, 3, and 4**.

## Project Structure

The repository currently contains two implementations/stages of the project:

```text
Jump-Up/
├── Python (Pygame)/
│   ├── jumpup.py
│   ├── runner.py
│   ├── player.py
│   ├── character.py
│   ├── diamond.py
│   ├── constants.py
│   ├── color_generator.py
│   ├── modal.py
│   ├── utils.py
│   ├── houses/
│   │   ├── heart.txt
│   │   ├── square.txt
│   │   └── rect.txt
│   └── static/
│       └── images/
│
└── Mobile App (React Native)/
    └── jump-up/
        ├── app/
        ├── assets/
        ├── package.json
        └── app.json
```

### Python / Pygame

The Python implementation is the original gameplay prototype. It provides the main reference for the game's original concepts, layouts, player/stone objects, game states, and visual direction.

Some parts of the prototype are incomplete and should therefore be treated as a **gameplay reference**, not as the final implementation of every rule.

### React Native / Expo

The React Native application is the newer mobile target. It is being developed to turn Jump-Up into a proper mobile game while preserving the traditional gameplay rules.

## Development Direction

The mobile version should not be a generic hopscotch game or a direct line-by-line port of the Python prototype.

The goal is to build a faithful digital version of **Jump-Up as it is traditionally played**, while providing a polished mobile experience.

The implementation should be built around a clear game model containing concepts such as:

- House layouts and individual house boundaries
- Players and turn order
- Individual player stones
- Stone throwing and validation
- One-leg hopping and movement
- Boundary/line collision rules
- House ownership
- Resting in owned houses
- House selection/claiming rules
- Turn progression and failure
- Multiplayer support
- AI opponents
- Game completion and winner calculation

## Current Status

The repository is currently in the process of transitioning from the original Pygame prototype to the React Native/Expo mobile implementation.

The **Python prototype is the historical gameplay reference**, while the **React Native application is the target platform for the new implementation**.

## Project Goal

The long-term goal is to create a fun, accessible mobile version of a traditional Nigerian game and preserve the core experience digitally:

> **Throw the stone. Hop through the houses. Claim your houses. Keep playing until you fail. Own the most houses and win.**
