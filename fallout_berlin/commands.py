from abc import ABC, abstractmethod
from typing import List, Optional
import random
from colorama import Fore, Style
from fallout_berlin.events import Event, EventType
from fallout_berlin.enemy import create_enemy


class Command(ABC):
    """Abstract base class for all commands"""

    @abstractmethod
    def execute(self, game_engine):
        pass


class MoveCommand(Command):
    def __init__(self, direction: str = ""):
        self.direction = direction

    def execute(self, game):
        location = game.location_manager.get_location(game.state.current_location)
        if not location:
            return

        # Check encumbrance
        if game.state.inventory and game.state.player and game.state.player.is_overencumbered(
            game.state.inventory.get_total_weight()
        ):
            print(
                f"{Fore.RED}You are overencumbered and cannot move! Drop some items.{Style.RESET_ALL}"
            )
            return

        dir_choice = (self.direction or "").strip().lower()

        # If no direction provided or generic verb, show numbered interactive menu
        if not dir_choice or dir_choice in ["go", "move", "travel"]:
            if not location.connections:
                print(f"{Fore.YELLOW}There are no exits from here.{Style.RESET_ALL}")
                return
            exits = list(location.connections.items())
            print(f"\n{Fore.CYAN}Available Destinations:{Style.RESET_ALL}")
            for i, (direction, dest_id) in enumerate(exits, 1):
                dest_loc = game.location_manager.get_location(dest_id)
                dest_name = dest_loc.name if dest_loc else dest_id.replace("_", " ").title()
                danger = ""
                if dest_loc and dest_loc.get_property("hostile", False):
                    danger = f" {Fore.RED}[DANGER]{Style.RESET_ALL}"
                elif dest_loc and dest_loc.get_property("radiation_level", 0) >= 20:
                    danger = f" {Fore.GREEN}[RADS]{Style.RESET_ALL}"
                print(f"  {Fore.YELLOW}[{i}]{Style.RESET_ALL} {direction.capitalize()} -> {dest_name}{danger}")
            try:
                pick = input(f"\nSelect exit [1-{len(exits)}] or direction: ").strip().lower()
                if pick.isdigit() and 1 <= int(pick) <= len(exits):
                    dir_choice = exits[int(pick) - 1][0]
                elif pick:
                    dir_choice = pick
                else:
                    print("Travel cancelled.")
                    return
            except (EOFError, KeyboardInterrupt):
                return

        # Map direction aliases
        dir_aliases = {
            "n": "north", "s": "south", "e": "east", "w": "west",
            "u": "up", "d": "down"
        }
        dir_choice = dir_aliases.get(dir_choice, dir_choice)

        # Allow numbered exit selection directly (e.g. 'move 1' or '1')
        if dir_choice.isdigit() and location.connections:
            exits = list(location.connections.keys())
            idx = int(dir_choice) - 1
            if 0 <= idx < len(exits):
                dir_choice = exits[idx]

        destination_id = game.location_manager.can_travel(
            game.state.current_location, dir_choice
        )
        if destination_id:
            # Danger check / warning for low-level players entering lethal zones
            if destination_id == "museum_island" and game.state.player and game.state.player.level < 6:
                print(f"\n{Fore.RED}[DANGER WARNING] Ahead lies Museum Island—a heavily fortified Super Mutant stronghold.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Recommended Level: 8+. You are Level {game.state.player.level}.{Style.RESET_ALL}")
                try:
                    confirm = input("Are you sure you want to proceed into lethal territory? (y/N): ").strip().lower()
                    if confirm not in ['y', 'yes']:
                        print("You wisely step back.")
                        return
                except (EOFError, KeyboardInterrupt):
                    return

            # Restricted zones
            restricted_zones = {
                "checkpoint_charlie_inner": ["permit_a38", "us_passport"],
                "reichstag": ["anmeldung_form", "bureaucrat_pass"]
            }
            if destination_id in restricted_zones:
                required_items = restricted_zones[destination_id]
                has_access = False
                if game.state.inventory:
                    for item_id in required_items:
                        if game.state.inventory.find_item(item_id) or game.state.inventory.find_item(item_id.replace("_", " ")):
                            has_access = True
                            break
                if not has_access:
                    print(f"{Fore.RED}[HALT] Restricted Area: {destination_id.replace('_', ' ').title()}{Style.RESET_ALL}")
                    print(f"The guards block your path. \"Papers, please! You need: {', '.join(required_items).replace('_', ' ')}\"")
                    return

            # Sync old location before leaving
            game._sync_location_state()

            game.state.current_location = destination_id
            game.location_manager.visit_location(destination_id)
            print(f"You travel {dir_choice}...")

            # Survival Tick
            game._update_survival(move_cost=True)

            # Dispatch location enter event
            game.event_manager.dispatch(
                Event(EventType.LOCATION_ENTER, {"location_id": destination_id})
            )

            # Load location state if it exists
            if destination_id in game.state.location_states:
                from fallout_berlin.location import Location
                loc = Location.from_dict(game.state.location_states[destination_id])
                game.location_manager.add_location(loc)

            # Handle radiation
            new_location = game.location_manager.get_location(destination_id)
            if new_location:
                rad_level = new_location.get_property("radiation_level", 0)
                if rad_level > 0 and game.state.player:
                    rad_gain = max(1, rad_level // 10)
                    died_from_rad = game.state.player.take_radiation(rad_gain)
                    if rad_gain > 0:
                        print(
                            f"[!] You absorbed {Fore.RED}{rad_gain}{Style.RESET_ALL} rads from the environment."
                        )
                    if died_from_rad:
                        game._handle_game_over(cause="Lethal radiation poisoning")
                        return

            # Scripted location enemies take priority over random encounters.
            if game._check_location_enemies(destination_id):
                game.state.player.is_sneaking = False
                return

            # Check for encounters
            encounter_chance = (
                0.1 if getattr(game.state.player, "is_sneaking", False) else 0.2
            )
            if game._check_random_encounter(chance=encounter_chance):
                game.state.player.is_sneaking = False  # Combat breaks stealth
                return
        else:
            print(f"You can't go '{self.direction}' from here.")


class LookCommand(Command):
    def __init__(self, target: Optional[str] = None):
        self.target = target

    def execute(self, game):
        location = game.location_manager.get_location(game.state.current_location)
        if not location:
            return

        if not self.target:
            # Refresh location view with ASCII art (force_art=True)
            game.ui_manager.display_location(
                location,
                weather=getattr(game, "current_weather", None),
                time_of_day=getattr(game, "time_of_day", "day"),
                force_art=True
            )
            return

        target_lower = self.target.lower()

        # Check inventory
        if game.state.inventory:
            item = game.state.inventory.find_item(target_lower)
            if item:
                print(game.state.inventory.display_item_details(item.name))
                input("\nPress Enter to continue...")
                return

        # Check items on ground
        item = location.find_item(target_lower)
        if item:
            print(f"\n[{item.name} (on the ground)]")
            print(item.description)
            input("\nPress Enter to continue...")
            return

        # Check enemies
        enemy = location.find_enemy(target_lower)
        if enemy:
            print(f"\n[{enemy.name}]")
            print(enemy.description)
            print(f"Level: {enemy.level} | HP: {enemy.hp}/{enemy.max_hp}")
            input("\nPress Enter to continue...")
            return

        # Check for NPCs
        if target_lower in [npc.lower() for npc in location.npcs]:
            print(f"\nYou see {self.target}. Maybe you should 'talk' to them.")
            input("\nPress Enter to continue...")
            return

        print(f"You don't see any '{self.target}' here.")
        input("\nPress Enter to continue...")


class TakeCommand(Command):
    def __init__(self, target: Optional[str] = None):
        self.target = target

    def execute(self, game):
        location = game.location_manager.get_location(game.state.current_location)
        if not location:
            return

        if not location.items:
            print(f"{Fore.YELLOW}There is nothing here to take.{Style.RESET_ALL}")
            return

        if not self.target:
            if len(location.items) == 1:
                item = location.remove_item(location.items[0].name)
                if item:
                    if game.state.inventory.add_item(item):
                        print(f"You take the {Fore.YELLOW}{item.name}{Style.RESET_ALL}.")
                        game._sync_location_state()
                        game._update_survival(move_cost=False)
                        game.event_manager.dispatch(
                            Event(EventType.ITEM_PICKUP, {"item": item})
                        )
                    else:
                        location.add_item(item)
                        print(f"{Fore.RED}You can't carry that. Your inventory is full.{Style.RESET_ALL}")
                return
            else:
                from fallout_berlin.looting_state import LootingState
                game.change_state(LootingState(game, location.name, location.items))
                return

        target_str = self.target.strip().lower()
        if target_str in ["all", "*"]:
            taken_any = False
            for item in list(location.items):
                if game.state.inventory.add_item(item):
                    location.remove_item(item.name)
                    print(f"You take the {Fore.YELLOW}{item.name}{Style.RESET_ALL}.")
                    taken_any = True
                else:
                    print(f"{Fore.RED}Cannot carry {item.name}: Inventory full.{Style.RESET_ALL}")
                    break
            if taken_any:
                game._sync_location_state()
                game._update_survival(move_cost=False)
            return

        item_name = self.target
        if self.target.isdigit():
            idx = int(self.target) - 1
            if 0 <= idx < len(location.items):
                item_name = location.items[idx].name
            else:
                print(f"{Fore.RED}Invalid item number.{Style.RESET_ALL}")
                return

        item = location.remove_item(item_name)
        if item:
            if game.state.inventory.add_item(item):
                print(f"You take the {Fore.YELLOW}{item.name}{Style.RESET_ALL}.")
                game._sync_location_state()
                game._update_survival(move_cost=False)
                game.event_manager.dispatch(
                    Event(EventType.ITEM_PICKUP, {"item": item})
                )
            else:
                location.add_item(item)
                print(
                    f"{Fore.RED}You can't carry that. Your inventory is too full.{Style.RESET_ALL}"
                )
        else:
            print(f"{Fore.YELLOW}You don't see '{item_name}' here.{Style.RESET_ALL}")


class LootCommand(Command):
    def execute(self, game):
        location = game.location_manager.get_location(game.state.current_location)
        if location and location.items:
            from fallout_berlin.looting_state import LootingState
            game.change_state(LootingState(game, location.name, location.items))
        else:
            print(f"{Fore.YELLOW}There is nothing here to loot.{Style.RESET_ALL}")


class UseCommand(Command):
    def __init__(self, target: Optional[str], indirect: Optional[str] = None):
        self.target = target
        self.indirect = indirect

    def execute(self, game):
        if not game.state.inventory:
            return

        if not self.target:
            consumables = [
                i for i in game.state.inventory.items if i.item_type == "consumable"
            ]
            if not consumables:
                print("You have no usable items.")
            else:
                print("\nConsumables:")
                for i, item in enumerate(consumables, 1):
                    print(f"{i}. {item.name} ({item.effect_type}: {item.effect_value})")
                print("\nUsage: use <item> [on <target>]")
            return

        item = None
        if self.target.isdigit():
            consumables = [
                i for i in game.state.inventory.items if i.item_type == "consumable"
            ]
            idx = int(self.target) - 1
            if 0 <= idx < len(consumables):
                item = consumables[idx]
            else:
                print("Invalid item number.")
                return
        else:
            item = game.state.inventory.find_item(self.target)

        if not item:
            print(f"You don't have '{self.target}'.")
            return

        if self.indirect:
            if self.indirect in ["self", "player", "me"]:
                if item.item_type == "consumable":
                    game._use_consumable(item)
                else:
                    print(f"You can't use {item.name} on yourself.")
            else:
                game._handle_interaction(item, self.indirect)
        else:
            if item.item_type == "consumable":
                game._use_consumable(item)
            elif item.name == "Anmeldung Form 27-B":
                game._handle_form_filling(item)
            else:
                print(
                    f"You can't use {item.name} like that. Maybe try using it ON something?"
                )


class TalkCommand(Command):
    def __init__(self, target: Optional[str] = None):
        self.target = target

    def execute(self, game):
        location = game.location_manager.get_location(game.state.current_location)
        if not location or not location.npcs:
            print(f"{Fore.YELLOW}There is no one here to talk to.{Style.RESET_ALL}")
            return

        from fallout_berlin.ui import UIManager
        npc_list = location.npcs

        target_npc = None
        if not self.target or not self.target.strip():
            if len(npc_list) == 1:
                target_npc = npc_list[0]
            else:
                print(f"\n{Fore.CYAN}Who would you like to speak with?{Style.RESET_ALL}")
                for i, npc_id in enumerate(npc_list, 1):
                    name = UIManager.get_npc_name(npc_id)
                    print(f"  {Fore.YELLOW}[{i}]{Style.RESET_ALL} {name}")
                try:
                    choice = input(f"\nSelect [1-{len(npc_list)}] or press Enter to cancel: ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(npc_list):
                        target_npc = npc_list[int(choice) - 1]
                    else:
                        print("Conversation cancelled.")
                        return
                except (EOFError, KeyboardInterrupt):
                    return
        elif self.target.isdigit():
            idx = int(self.target) - 1
            if 0 <= idx < len(npc_list):
                target_npc = npc_list[idx]
            else:
                print(f"{Fore.RED}Invalid NPC number.{Style.RESET_ALL}")
                return
        else:
            search = self.target.lower().strip()
            for npc_id in npc_list:
                display_name = UIManager.get_npc_name(npc_id).lower()
                if search in npc_id.lower() or search in display_name or npc_id.lower() in search:
                    target_npc = npc_id
                    break

        if not target_npc:
            print(f"{Fore.YELLOW}You don't see '{self.target}' here.{Style.RESET_ALL}")
            return

        # Faction Hostility check
        faction_map = {
            "guard": "Iron Ring",
            "soldier": "Iron Ring",
            "officer": "Iron Ring",
            "ghoul": "Schattenvolk",
            "shadow": "Schattenvolk",
            "commune": "Feld Commune",
            "farmer": "Feld Commune",
            "knight": "Bundesritter",
            "squire": "Bundesritter",
            "breaker": "Wall Breakers",
            "raider": "Wall Breakers",
            "punk": "Wall Breakers",
            "merchant": "Werkbund",
            "smith": "Werkbund",
            "dealer": "Schattenvolk"
        }
        target_faction = None
        for key, faction in faction_map.items():
            if key in target_npc.lower():
                target_faction = faction
                break

        if target_faction and game.state.get_faction_reputation(target_faction) <= -50:
            print(
                f"{Fore.RED}The {target_npc} recognizes you as an enemy of {target_faction}! They attack!{Style.RESET_ALL}"
            )
            enemy = create_enemy("raider_scum")
            if enemy:
                enemy.name = UIManager.get_npc_name(target_npc)
                game.start_combat(enemy)
            return

        game._start_dialogue(target_npc)


class InventoryCommand(Command):
    def execute(self, game):
        from fallout_berlin.inventory_state import InventoryState
        game.change_state(InventoryState(game))


class StatsCommand(Command):
    def execute(self, game):
        game.ui_manager.show_stats()
        input("\nPress Enter to continue...")


class QuestsCommand(Command):
    def execute(self, game):
        from fallout_berlin.quest_log_state import QuestLogState
        game.change_state(QuestLogState(game))


class HelpCommand(Command):
    def execute(self, game):
        game.ui_manager.show_help("exploration")
        input("\nPress Enter to continue...")


class EquipCommand(Command):
    def __init__(self, target: str):
        self.target = target

    def execute(self, game):
        if not game.state.player or not game.state.inventory:
            print(f"{Fore.RED}Error: Player or Inventory not available.{Style.RESET_ALL}")
            return

        item_name = self.target
        item_to_equip = game.state.inventory.find_item(item_name)

        if not item_to_equip:
            print(f"{Fore.YELLOW}You don't have '{item_name}' in your inventory.{Style.RESET_ALL}")
            return

        from fallout_berlin.item import Weapon, Armor # Import here to avoid circular dependency issues

        if isinstance(item_to_equip, Weapon):
            game.state.player.equipped_weapon = item_to_equip
            print(f"You equip the {Fore.GREEN}{item_to_equip.name}{Style.RESET_ALL}.")
        elif isinstance(item_to_equip, Armor):
            game.state.player.equipped_armor = item_to_equip
            print(f"You equip the {Fore.GREEN}{item_to_equip.name}{Style.RESET_ALL}.")
        else:
            print(f"{Fore.YELLOW}You cannot equip '{item_to_equip.name}'.{Style.RESET_ALL}")
            return
        
        # Recalculate player stats as equipment affects derived stats (e.g., carry weight, DR)
        game.state.player._calculate_derived_stats()
        game.event_manager.dispatch(
            Event(EventType.ITEM_EQUIP, {"item": item_to_equip, "player": game.state.player})
        )
        game._update_survival(move_cost=False) # Equipping might take a tiny bit of time

class CraftCommand(Command):
    def __init__(self, target: Optional[str] = None):
        self.target = target

    def execute(self, game):
        if not self.target:
            from fallout_berlin.crafting_state import CraftingState
            game.change_state(CraftingState(game))
        else:
            game._handle_craft(self.target.split())


class SneakCommand(Command):
    def execute(self, game):
        game._handle_sneak()


class CampCommand(Command):
    def execute(self, game):
        game._handle_camp()


class RadioCommand(Command):
    def execute(self, game):
        game._handle_radio()


class CompanionCommand(Command):
    def __init__(self, args: List[str]):
        self.args = args

    def execute(self, game):
        game._handle_companion(self.args)


class StealCommand(Command):
    def __init__(self, args: List[str]):
        self.args = args

    def execute(self, game):
        game._handle_steal(self.args)


class HackCommand(Command):
    def __init__(self, args: List[str]):
        self.args = args

    def execute(self, game):
        game._handle_hack(self.args)


class ScanCommand(Command):
    def execute(self, game):
        game._handle_scan()


class MapCommand(Command):
    def execute(self, game):
        location = game.location_manager.get_location(game.state.current_location)
        if location:
            game.ui_manager.draw_mini_map(location)
            input("\nPress Enter to continue...")


class SaveCommand(Command):
    def execute(self, game):
        game._save_game()


class LoadCommand(Command):
    def execute(self, game):
        game._load_game()


class QuitCommand(Command):
    def execute(self, game):
        game._quit_game()


class SettingsCommand(Command):
    def execute(self, game):
        game.ui_manager.show_settings_menu()

class PauseCommand(Command):
    def execute(self, game):
        from fallout_berlin.engine_states import PauseMenuState
        game.change_state(PauseMenuState(game))


class CombatPlaceholderCommand(Command):
    def execute(self, game):
        print("Command not available in exploration mode.")


class AttackCommand(Command):
    def __init__(self, target: Optional[str] = None):
        self.target = target

    def execute(self, game):
        location = game.location_manager.get_location(game.state.current_location)
        enemies = location.enemies if location else []
        if self.target:
            target = self.target.casefold()
            enemy = next(
                (
                    enemy
                    for enemy in enemies
                    if enemy.name.casefold() == target
                    or str(getattr(enemy, "enemy_id", "")).casefold() == target
                ),
                None,
            )
            if enemy:
                game.start_combat(enemy)
            else:
                print(f"You don't see '{self.target}' here.")
            return

        if len(enemies) == 1:
            game.start_combat(enemies[0])
        elif enemies:
            names = ", ".join(enemy.name for enemy in enemies)
            print(f"Enemies here: {names}. Use 'attack [enemy name]' to engage.")
        else:
            print("There are no enemies here to attack.")


class CutsceneCommand(Command):
    def __init__(self, scene_id: str):
        self.scene_id = scene_id

    def execute(self, game):
        game.cutscene_manager.play_cutscene(self.scene_id)