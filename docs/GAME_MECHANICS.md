# Fallout: Berlin - Game Mechanics Documentation

## Overview

This document describes all the game mechanics implemented for Fallout: Berlin. The game is built as a modular Python system with clear separation of concerns.

## Core Systems

### 1. Game State Management (`game_state.py`)

**Purpose**: Central state management and save/load functionality

**Key Features**:
- Tracks player, inventory, location, quests, and world state
- Faction reputation system (-100 to +100)
- World flags for tracking story events
- JSON-based save/load system
- Multiple save file support

**Usage**:
```python
state = GameState()
state.save_game("my_save.json")
state.load_game("my_save.json")
```

### 2. Player System (`player.py`)

**Purpose**: Character creation, stats, and progression

**Key Features**:
- **S.P.E.C.I.A.L. Stats**: Strength, Perception, Endurance, Charisma, Intelligence, Agility, Luck (1-10 each)
- **Skills**: 18 skills based on Fallout (Small Guns, Science, Speech, etc.)
- **Character Origins**: 6 different origins with unique bonuses
- **Level System**: Experience points and leveling
- **Health & Radiation**: Hit points and radiation tracking
- **Derived Stats**: Action points, carry weight calculated from S.P.E.C.I.A.L.

**Character Origins**:
- Vault Dweller: Science, Repair, First Aid bonuses
- Wastelander: Outdoorsman, Sneak bonuses
- Ghoul: Radiation resistance, unique abilities
- Raider: Combat skills
- Trader: Barter, Speech bonuses
- Scientist: Science, Repair, Doctor bonuses

**Skill System**:
- Base skill = (Primary S.P.E.C.I.A.L. stat × 2) + 5
- Origin bonuses added on top
- Skills range from 0-200
- Skill checks: Roll 1-100 + skill value vs difficulty

### 3. Item System (`item.py`)

**Purpose**: Items, weapons, armor, consumables

**Item Types**:
- **Weapon**: Damage, weapon type, skill required, ammo type
- **Armor**: Damage resistance, armor type
- **Consumable**: Effect type (heal, rad_heal, buff), effect value
- **Ammo**: Ammunition for ranged weapons
- **Misc**: General items

**Item Database**: Pre-defined items including:
- Weapons: 10mm Pistol, Pipe Pistol, Knife, Laser Rifle
- Armor: Vault Suit, Leather Armor, Raider Armor
- Consumables: Stimpak, RadAway, Rad-X
- Ammo: 10mm Rounds, Fusion Cells

### 4. Inventory System (`inventory.py`)

**Purpose**: Item management and weight tracking

**Key Features**:
- Weight-based capacity (default 150 lbs)
- Stackable items (ammo, consumables)
- Item type filtering (weapons, armor, consumables, ammo)
- Ammo tracking and usage
- Display formatting

**Methods**:
- `add_item(item)`: Add item (checks weight)
- `remove_item(name, quantity)`: Remove items
- `has_item(name, quantity)`: Check for items
- `get_ammo_count(type)`: Get ammo quantity
- `use_ammo(type, amount)`: Consume ammunition

### 5. Location System (`location.py`)

**Purpose**: World navigation and area management

**Key Features**:
- Location connections (north, south, east, west)
- Items in locations
- Location properties (radiation, safety, discovered status)
- Custom actions per location
- Location events

**Location Manager**:
- Manages all game locations
- Handles travel between locations
- Tracks discovered/visited locations
- Initial locations: Checkpoint Charlie Market, The Wasteland

### 6. Dialogue System (`dialogue.py`)

**Purpose**: NPC conversations and dialogue trees

**Key Features**:
- Dialogue trees with nodes and options
- Conditional dialogue (skill checks, faction rep, items, quests)
- Dialogue actions (can trigger game events)
- Multiple dialogue paths

**Dialogue Structure**:
- **DialogueTree**: Complete conversation for an NPC
- **DialogueNode**: Single dialogue exchange
- **DialogueOption**: Player response choice
- **DialogueCondition**: Requirements for options to appear

**Example Conditions**:
- Skill checks (e.g., Speech 50+)
- Faction reputation (e.g., Iron Curtain rep 25+)
- Item requirements (e.g., has "Key Card")
- Quest state (e.g., quest "first_steps" active)
- World flags

### 7. Quest System (`quest.py`)

**Purpose**: Quest tracking and objectives

**Key Features**:
- Quest states: Not Started, Active, Completed, Failed
- Multiple objectives per quest
- Optional objectives
- Quest rewards (XP, caps, items, faction rep)
- Quest notes and descriptions

**Quest Structure**:
- **Quest**: Main quest container
- **QuestObjective**: Individual objectives
- **QuestManager**: Manages all quests

**Example Quest**: "First Steps"
- Explore Checkpoint Charlie Market
- Talk to a trader
- Learn about the factions
- Rewards: 100 XP, 50 caps

### 8. Game Engine (`game_engine.py`)

**Purpose**: Main game loop, command parsing, UI

**Key Features**:
- Command parser for player input
- Game loop with location display
- Character creation flow
- Dialogue handling
- Save/load menu
- Help system

**Commands**:
- **Movement**: `go [direction]`, `north`, `south`, `east`, `west`
- **Inventory**: `inventory`, `inv`, `i`
- **Stats**: `stats`, `character`, `char`
- **Interaction**: `look`, `take [item]`, `use [item]`, `talk [npc]`
- **Quests**: `quest`, `quests`, `q`
- **Game**: `save`, `load`, `help`, `quit`

**Game Flow**:
1. Character creation (name, origin, S.P.E.C.I.A.L.)
2. Starting location assignment
3. Main game loop:
   - Display location
   - Get player command
   - Process command
   - Update game state
   - Repeat

## Data Flow

```
GameEngine
    ├── GameState (save/load, world state)
    ├── Player (character stats, skills)
    ├── Inventory (items, weight)
    ├── LocationManager (navigation)
    ├── DialogueManager (conversations)
    └── QuestManager (quests, objectives)
```

## Save System

**Format**: JSON files in `saves/` directory

**Saved Data**:
- Player character (stats, skills, level, XP)
- Current location
- Inventory (all items)
- Faction reputation
- Quest states and progress
- World flags
- Visited/discovered locations

**Load Process**:
1. Read JSON file
2. Reconstruct Player object
3. Reconstruct Inventory with items
4. Reconstruct Quests
5. Restore world state

## Extensibility

### Adding New Locations
```python
new_location = Location(
    "Location Name",
    "Description",
    "location_id"
)
location_manager.add_location(new_location)
```

### Adding New Items
```python
ITEM_DATABASE['new_item'] = Weapon(
    'New Weapon',
    'Description',
    damage=20,
    weapon_type='ranged',
    skill='Small Guns',
    ammo_type='10mm'
)
```

### Adding New Quests
```python
new_quest = Quest("quest_id", "Title", "Description")
new_quest.add_objective(QuestObjective("Do something"))
quest_manager.add_quest(new_quest)
```

### Adding Dialogue
```python
tree = DialogueTree("npc_id", "NPC Name")
node = DialogueNode("start", "NPC", "Hello!")
node.add_option(DialogueOption("Hi!", "next_node"))
tree.add_node(node)
dialogue_manager.add_dialogue_tree(tree)
```

## Future Enhancements

Potential additions:
- Combat system (turn-based or real-time)
- Random encounters
- Crafting system
- More locations and NPCs
- Expanded quest lines
- Multiple endings
- Achievement system
- Character perks/traits

## Testing

To test the game:
1. Run `python run_game.py` or `python -m fallout_berlin.game_engine`
2. Create a character
3. Test commands: `look`, `inventory`, `stats`, `go north`
4. Test dialogue: `talk trader`
5. Test save/load: `save`, then `load`

## File Structure

```
fallout_berlin/
├── __init__.py          # Package initialization
├── game_state.py        # State management
├── player.py            # Character system
├── item.py              # Items and database
├── inventory.py         # Inventory management
├── location.py          # Locations and navigation
├── dialogue.py          # Dialogue system
├── quest.py             # Quest system
├── game_engine.py       # Main game loop
└── main.py              # Entry point
```

## Notes

- All systems are modular and can be extended independently
- No external dependencies (pure Python standard library)
- Save files are human-readable JSON
- Easy to add new content (locations, items, quests, dialogue)
