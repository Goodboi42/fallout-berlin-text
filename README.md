# Fallout: Berlin - Text-Based Adventure

A text-based adventure game set in the Fallout universe, taking place in post-nuclear Berlin.

## Features

- **Character Creation**: Choose your origin and allocate S.P.E.C.I.A.L. stats
- **Inventory System**: Manage items, weapons, armor, and consumables
- **Quest System**: Track objectives and complete quests
- **Dialogue System**: Interactive conversations with NPCs
- **Faction Reputation**: Your actions affect how factions view you
- **Location Exploration**: Navigate the wasteland of Berlin
- **Save/Load**: Save your progress and continue later

## Installation

No external dependencies required! Uses only Python standard library.

## Running the Game

```bash
python -m fallout_berlin.main
```

Or:

```bash
python -m fallout_berlin.game_engine
```

## Game Commands

- **Movement**: `go [direction]`, `north`, `south`, `east`, `west` (or `n`, `s`, `e`, `w`)
- **Inventory**: `inventory`, `inv`, `i`
- **Stats**: `stats`, `character`, `char`
- **Interaction**: `look`, `take [item]`, `use [item]`, `talk [npc]`
- **Quests**: `quest`, `quests`, `q`
- **Game**: `save`, `load`, `help`, `quit`

## Game Structure

```
fallout_berlin/
├── game_state.py      # Game state management and save/load
├── player.py          # Player character and S.P.E.C.I.A.L. system
├── item.py            # Items, weapons, armor, consumables
├── inventory.py       # Inventory management
├── location.py        # Locations and navigation
├── dialogue.py        # Dialogue system and NPC conversations
├── quest.py           # Quest system and objectives
├── game_engine.py     # Main game loop and command parser
└── main.py            # Entry point
```

## Character Origins

- **Vault Dweller**: Grew up safe in Vault 17-Berlin
- **Wastelander**: Survived in the wasteland
- **Ghoul**: Radiation survivor with unique abilities
- **Raider**: Former raider, now on your own
- **Trader**: Made your living trading
- **Scientist**: Researcher with technical knowledge

## Development Status

This is an early version with core mechanics implemented. Future updates will include:
- More locations and NPCs
- Expanded quest lines
- Combat system
- More items and equipment
- Random encounters
- Multiple endings

## License

This is a fan project set in the Fallout universe. Fallout is a trademark of Bethesda Softworks.
