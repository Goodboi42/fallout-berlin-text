"""
Main Game Engine
Handles the game loop, command parsing, and UI
"""

import os
import sys
from typing import Optional, List, Dict
from fallout_berlin.game_state import GameState
from fallout_berlin.player import Player
from fallout_berlin.inventory import Inventory
from fallout_berlin.location import LocationManager
from fallout_berlin.dialogue import DialogueManager
from fallout_berlin.quest import QuestManager
from fallout_berlin.item import create_item, ITEM_DATABASE
from fallout_berlin.enemy import create_enemy, Enemy
from fallout_berlin.crafting import CraftingManager
import random


class GameEngine:
    """Main game engine"""
    
    def __init__(self):
        self.state = GameState()
        self.location_manager = LocationManager()
        self.dialogue_manager = DialogueManager()
        self.quest_manager = QuestManager()
        self.crafting_manager = CraftingManager()
        self.running = False
        self.in_dialogue = False
        self.in_combat = False
        self.current_dialogue_tree = None
        self.current_dialogue_node = None
        self.current_enemy = None
    
    def start_new_game(self):
        """Start a new game"""
        print("\n" + "="*60)
        print("FALLOUT: BERLIN")
        print("="*60)
        print("\nWelcome to the wasteland, survivor.")
        print("The year is 2287. Berlin lies in ruins, divided by old walls")
        print("and new conflicts. Your story begins here...\n")
        
        # Character creation
        self._character_creation()
        
        # Initialize game state
        self.state.player = self.player
        self.state.inventory = Inventory(max_weight=self.player.carry_weight)
        self.state.current_location = "checkpoint_charlie"
        
        # Add starting items based on origin
        origin_data = self.player.get_origin_data()
        if origin_data:
            for item_key in origin_data.get('starting_items', []):
                # Handle quantities (e.g., "Stimpak x3")
                if ' x' in item_key:
                    item_name, quantity = item_key.split(' x')
                    item = create_item(item_name.lower().replace(' ', '_'), int(quantity))
                else:
                    item = create_item(item_key.lower().replace(' ', '_'))
                
                if item:
                    self.state.inventory.add_item(item)
        
        # Start first quest
        self.quest_manager.start_quest("first_steps")
        self.state.quests = {q.quest_id: q for q in self.quest_manager.quests.values()}
        
        # Mark location as visited
        location = self.location_manager.get_location(self.state.current_location)
        if location:
            self.location_manager.visit_location(self.state.current_location)
        
        print("\n" + "="*60)
        print("GAME START")
        print("="*60 + "\n")
        
        self.running = True
        self.game_loop()
    
    def _start_combat(self, enemy: Enemy):
        """Start combat with an enemy"""
        self.in_combat = True
        self.current_enemy = enemy
        print(f"\n!!! COMBAT STARTED !!!")
        print(f"You are attacked by {enemy.name} (Level {enemy.level})!")
        self._show_combat_status()
    
    def _show_combat_status(self):
        """Show combat status"""
        if not self.current_enemy or not self.state.player:
            return
            
        print("\n" + "="*40)
        print(f"Enemy: {self.current_enemy.name} [HP: {self.current_enemy.hp}/{self.current_enemy.max_hp}]")
        print(f"You:   {self.state.player.name} [HP: {self.state.player.hit_points}/{self.state.player.max_hit_points}]")
        print("="*40)
        print("\nActions: [A]ttack, [H]eal, [F]lee")

    def _handle_combat_command(self, command: str):
        """Handle combat commands"""
        if command in ['a', 'attack', 'fight']:
            self._player_attack()
        elif command in ['h', 'heal', 'use stimpak']:
            self._player_heal()
        elif command in ['f', 'flee', 'run']:
            self._player_flee()
        else:
            print("Invalid combat command. Use 'attack', 'heal', or 'flee'.")
            return
            
        # If combat is still active, enemy turn
        if self.in_combat and self.current_enemy and self.current_enemy.is_alive:
            self._enemy_attack()
            self._show_combat_status()

    def _player_attack(self):
        """Player attacks the enemy"""
        if not self.state.player or not self.current_enemy:
            return
            
        weapon = self.state.player.equipped_weapon
        
        # Hit chance logic
        hit_chance = 60 + (self.state.player.agility * 3) + (self.state.player.luck)
        if weapon:
            skill_val = self.state.player.get_skill(weapon.skill)
            hit_chance += skill_val // 5
            
        roll = random.randint(1, 100)
        
        if roll > hit_chance:
            if roll >= 95:
                fumbles = [
                    "You stumble over a piece of pre-war rubble!",
                    "Your grip slips on the blood-slicked handle!",
                    "You get distracted by a flickering neon sign!",
                    "A sudden rad-cough ruins your aim!"
                ]
                print(f"\n[!] CRITICAL MISS: {random.choice(fumbles)}")
                self.state.player.take_damage(random.randint(2, 5))
            else:
                print(f"\nYou swing at the {self.current_enemy.name} but they dodge with a snarl!")
            return

        # Damage calculation
        if weapon:
            damage = weapon.damage
            verbs = ["blast", "strike", "pierce", "hit"] if weapon.weapon_type == 'ranged' else ["slash", "bash", "cut", "strike"]
            print(f"\nYou {random.choice(verbs)} the {self.current_enemy.name} with your {weapon.name}!")
        else:
            damage = 5
            print(f"\nYou throw a heavy punch at the {self.current_enemy.name}!")
        
        damage += self.state.player.strength // 2
        if weapon:
            skill_val = self.state.player.get_skill(weapon.skill)
            damage = int(damage * (1 + skill_val / 100))
        
        crit_chance = self.state.player.luck * 2
        is_crit = random.randint(1, 100) <= crit_chance
        
        if is_crit:
            damage *= 2
            crit_msgs = ["V.A.T.S. highlights a weakness!", "A direct hit to the head!", "Brutal impact!", "The strike finds a gap in the armor!"]
            print(f">>> {random.choice(crit_msgs)} You deal {damage} damage!")
        else:
            print(f"> You deal {damage} damage.")
            
        self.current_enemy.take_damage(damage)
        
        if not self.current_enemy.is_alive:
            self._end_combat(victory=True)

    def _player_heal(self):
        """Player uses a healing item"""
        # Check for stimpaks
        stimpak = self.state.inventory.find_item('stimpak')
        if stimpak:
            self._use_consumable(stimpak)
        else:
            print("\nYou have no Stimpaks!")

    def _player_flee(self):
        """Attempt to flee combat"""
        # Chance based on Agility
        flee_chance = self.state.player.agility * 10
        if random.randint(1, 100) <= flee_chance:
            print("\nYou managed to escape!")
            self._end_combat(victory=False, fled=True)
        else:
            print("\nFailed to escape!")

    def _enemy_attack(self):
        """Enemy attacks the player with descriptive combat"""
        if not self.current_enemy or not self.state.player:
            return
            
        damage = self.current_enemy.attack()
        
        # Damage reduction from armor
        dr = 0
        if self.state.player.equipped_armor:
            dr = self.state.player.equipped_armor.damage_resistance
            
        final_damage = max(1, damage - dr)
        
        # Visceral descriptions
        attack_desc = [
            f"The {self.current_enemy.name} lunges at you!",
            f"A vicious swipe from the {self.current_enemy.name} connects!",
            f"The {self.current_enemy.name} catches you off guard!"
        ]
        print(f"\n{random.choice(attack_desc)}")
        print(f"[-] You take {final_damage} damage (Armor absorbed {dr}).")
        
        self.state.player.take_damage(final_damage)
        
        if self.state.player.hit_points <= 0:
            print("\n" + "*" * 20)
            print("  YOU ARE DEAD  ")
            print("*" * 20)
            print("The Berlin wasteland claims another soul.")
            self.running = False

    def _end_combat(self, victory: bool, fled: bool = False):
        """End combat session"""
        self.in_combat = False
        
        if victory:
            print(f"\nYou defeated {self.current_enemy.name}!")
            # Award XP
            self.state.player.add_experience(self.current_enemy.xp_reward)
            
            # Loot
            loot = self.current_enemy.get_loot()
            if loot:
                print("Loot found:")
                for item in loot:
                    if self.state.inventory.add_item(item):
                        print(f"  - {item.name}")
                    else:
                        print(f"  - {item.name} (Inventory full)")
                        # Drop to location
                        location = self.location_manager.get_location(self.state.current_location)
                        if location:
                            location.add_item(item)
            
            # Remove enemy from location if it was a persistent enemy
            # (Random encounters aren't in the location list usually, but handled here for completeness)
            location = self.location_manager.get_location(self.state.current_location)
            if location:
                 location.remove_enemy(self.current_enemy.name)
            
            self._sync_location_state()

        elif fled:
            print("You ran away to fight another day.")
            
        self.current_enemy = None
        input("\nPress Enter to continue...")

    def _character_creation(self):
        """Handle character creation"""
        print("\n=== CHARACTER CREATION ===\n")
        
        # Get name
        name = input("What is your name? ").strip()
        if not name:
            name = "Wanderer"
        
        self.player = Player(name)
        
        # Choose origin
        print("\nChoose your origin:")
        origins = list(Player.ORIGINS.keys())
        for i, origin_key in enumerate(origins, 1):
            origin_data = Player.ORIGINS[origin_key]
            print(f"{i}. {origin_data['name']}")
            print(f"   {origin_data['description']}")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-{}): ".format(len(origins))).strip()
                choice_num = int(choice)
                if 1 <= choice_num <= len(origins):
                    origin_key = origins[choice_num - 1]
                    self.player.set_origin(origin_key)
                    origin_data = Player.ORIGINS[origin_key]
                    print(f"\nYou are a {origin_data['name']}.")
                    break
                else:
                    print("Invalid choice. Please try again.")
            except ValueError:
                print("Please enter a number.")
        
        # S.P.E.C.I.A.L. point allocation
        print("\n=== S.P.E.C.I.A.L. STATS ===")
        print("You have 5 points to distribute among your S.P.E.C.I.A.L. stats.")
        print("Each stat starts at 5. You can increase any stat up to 10.")
        print("(Stats: Strength, Perception, Endurance, Charisma, Intelligence, Agility, Luck)\n")
        
        points_remaining = 5
        stats = ['strength', 'perception', 'endurance', 'charisma', 'intelligence', 'agility', 'luck']
        
        while points_remaining > 0:
            print(f"\nPoints remaining: {points_remaining}")
            print("Current stats:")
            for stat in stats:
                value = getattr(self.player, stat)
                print(f"  {stat.capitalize()}: {value}")
            
            stat_name = input("\nWhich stat would you like to increase? ").strip().lower()
            if stat_name in stats:
                current_value = getattr(self.player, stat_name)
                if current_value >= 10:
                    print(f"{stat_name.capitalize()} is already at maximum (10).")
                else:
                    self.player.set_special(stat_name, current_value + 1)
                    points_remaining -= 1
            else:
                print("Invalid stat name. Please try again.")
        
        print("\n" + self.player.get_stat_summary())
        input("\nPress Enter to begin your journey...")
    
    def game_loop(self):
        """Main game loop"""
        while self.running:
            try:
                if not self.in_combat and not self.in_dialogue:
                    self._display_location()
                
                command = input("\n> ").strip().lower()
                
                if not command:
                    continue
                
                if self.in_combat:
                    self._handle_combat_command(command)
                elif self.in_dialogue:
                    self._handle_dialogue_command(command)
                else:
                    self._handle_command(command)
                    
            except KeyboardInterrupt:
                print("\n\nGame interrupted. Saving...")
                self._save_game_prompt()
                break
            except Exception as e:
                print(f"\nError: {e}")
                import traceback
                traceback.print_exc()
    
    def _handle_equip(self, args: List[str]):
        """Handle equip command"""
        if not args:
            print("Equip what?")
            return
        
        item_name = ' '.join(args)
        item = self.state.inventory.find_item(item_name) if self.state.inventory else None
        
        if not item:
            print(f"You don't have {item_name}.")
            return
        
        from fallout_berlin.item import Weapon, Armor
        if isinstance(item, Weapon):
            # Unequip current weapon if any
            if self.state.player.equipped_weapon:
                self.state.player.equipped_weapon.equipped = False
            
            self.state.player.equipped_weapon = item
            item.equipped = True
            print(f"You wield the {item.name}.")
        elif isinstance(item, Armor):
            # Unequip current armor if any
            if self.state.player.equipped_armor:
                self.state.player.equipped_armor.equipped = False
                
            self.state.player.equipped_armor = item
            item.equipped = True
            print(f"You put on the {item.name}.")
        else:
            print(f"You can't equip {item.name}.")

    def _handle_craft(self, args: List[str]):
        """Handle crafting command"""
        if not args:
            # Show available recipes
            available = self.crafting_manager.get_available_recipes(self.state.inventory, self.state.player)
            print("\n=== CRAFTING ===")
            if not available:
                print("You don't have enough materials or skill to craft anything right now.")
                print("All Recipes:")
                for rid, r in self.crafting_manager.recipes.items():
                    reqs = ", ".join([f"{n} x{q}" for n, q in r['requirements'].items()])
                    print(f"  - {r['name']} (ID: {rid}): {reqs}")
            else:
                print("You can craft:")
                for rid in available:
                    recipe = self.crafting_manager.recipes[rid]
                    print(f"  - {recipe['name']} (ID: {rid})")
            print("\nUsage: craft [recipe_id]")
            return

        recipe_id = args[0].lower()
        result = self.crafting_manager.craft(recipe_id, self.state.inventory, self.state.player)
        
        if result:
            print(f"\n[+] Successfully crafted: {result}")
        else:
            print(f"\n[-] You cannot craft '{recipe_id}'. Check materials and requirements.")

    def _sync_location_state(self):
        """Sync current location state to GameState for saving"""
        location = self.location_manager.get_location(self.state.current_location)
        if location:
            self.state.location_states[location.location_id] = location.to_dict()

    def _display_location(self):
        """Display current location with atmospheric UI"""
        if not self.state.current_location:
            return
            
        location = self.location_manager.get_location(self.state.current_location)
        if not location:
            return
        
        os.system('cls' if os.name == 'nt' else 'clear')
        
        # Atmospheric Border
        width = 65
        print("+" + "-" * (width-2) + "+")
        print("|" + f" {location.name} ".center(width-2, " ") + "|")
        print("+" + "-" * (width-2) + "+")
        
        # Location properties tags
        tags = []
        if location.get_property('radiation_level', 0) > 0:
            tags.append("[RADIOACTIVE]")
        if location.get_property('hostile', False):
            tags.append("[DANGER]")
        if not location.get_property('safe', True):
            tags.append("[UNSAFE]")
            
        if tags:
            print(" " + " ".join(tags))
            
        print(f"\n{location.description}")
        
        # Display surroundings
        if location.connections:
            print(f"\nExits: {', '.join(location.connections.keys())}")
            
        # Display objects of interest
        if location.items:
            print(f"You see: {', '.join([i.name for i in location.items])}")
        if location.enemies:
            print(f"Hostiles: {', '.join([e.name for e in location.enemies])}")
        
        # Player Vital HUD
        if self.state.player:
            p = self.state.player
            hp_bar = self._get_bar(p.hit_points, p.max_hit_points, 20)
            rad_bar = self._get_bar(p.radiation, p.max_radiation, 10, color="!")
            
            print("\n" + "=" * width)
            print(f" HP  [{hp_bar}] {p.hit_points}/{p.max_hit_points}")
            print(f" RAD [{rad_bar}] {p.radiation} rads")
            print(f" LVL {p.level} | XP {p.experience}/{p.experience_to_next}")
            
            eq_w = p.equipped_weapon.name if p.equipped_weapon else "None"
            print(f" WEAPON: {eq_w}")
            print("=" * width)

    def _get_bar(self, current, total, length, color="#") -> str:
        """Generate a text-based progress bar"""
        if total <= 0: return " " * length
        filled = int((current / total) * length)
        return color * filled + " " * (length - filled)
    
    def _handle_command(self, command: str):
        """Handle player commands"""
        parts = command.split()
        if not parts:
            return
        
        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        
        # Navigation
        if cmd in ['go', 'move', 'travel', 'north', 'south', 'east', 'west', 'n', 's', 'e', 'w']:
            self._handle_movement(cmd, args)
        
        # Inventory
        elif cmd in ['inventory', 'inv', 'i']:
            self._show_inventory()
        
        # Stats
        elif cmd in ['stats', 'stat', 'character', 'char']:
            self._show_stats()
        
        # Look/Examine
        elif cmd in ['look', 'examine', 'l']:
            self._handle_look(args)
        
        # Take/Get
        elif cmd in ['take', 'get', 'pickup']:
            self._handle_take(args)
        
        # Use
        elif cmd in ['use']:
            self._handle_use(args)
        
        # Equip
        elif cmd in ['equip', 'wear', 'wield']:
            self._handle_equip(args)
        
        # Craft
        elif cmd in ['craft', 'make', 'create']:
            self._handle_craft(args)
        
        # Talk/Speak
        elif cmd in ['talk', 'speak', 'say']:
            self._handle_talk(args)
        
        # Quests
        elif cmd in ['quest', 'quests', 'q']:
            self._show_quests()
        
        # Save
        elif cmd in ['save']:
            self._save_game()
        
        # Load
        elif cmd in ['load']:
            self._load_game()
        
        # Help
        elif cmd in ['help', 'h', '?']:
            self._show_help()
        
        # Quit
        elif cmd in ['quit', 'exit', 'q']:
            self._quit_game()
        
        else:
            print(f"I don't understand '{command}'. Type 'help' for available commands.")
    
    def _handle_movement(self, cmd: str, args: List[str]):
        """Handle movement commands with location state syncing"""
        location = self.location_manager.get_location(self.state.current_location)
        if not location:
            return
        
        # Determine direction
        direction = None
        if cmd in ['north', 'n']:
            direction = 'north'
        elif cmd in ['south', 's']:
            direction = 'south'
        elif cmd in ['east', 'e']:
            direction = 'east'
        elif cmd in ['west', 'w']:
            direction = 'west'
        elif cmd in ['go', 'move', 'travel'] and args:
            direction = args[0].lower()
        
        if not direction:
            print("Where do you want to go? (north, south, east, west)")
            return
        
        destination_id = self.location_manager.can_travel(self.state.current_location, direction)
        if destination_id:
            # Sync old location before leaving
            self._sync_location_state()
            
            self.state.current_location = destination_id
            self.location_manager.visit_location(destination_id)
            print(f"You travel {direction}...")
            
            # Quest objective: Explore market
            if destination_id == "checkpoint_charlie" and "first_steps" in self.state.quests:
                self.quest_manager.complete_objective("first_steps", "explore_market")
            
            # Load new location state if it exists
            if destination_id in self.state.location_states:
                from fallout_berlin.location import Location
                loc = Location.from_dict(self.state.location_states[destination_id])
                self.location_manager.add_location(loc)

            # Radiation accumulation logic
            new_location = self.location_manager.get_location(destination_id)
            if new_location:
                rad_level = new_location.get_property('radiation_level', 0)
                if rad_level > 0:
                    # Accumulate radiation based on location level
                    rad_gain = rad_level // 10
                    if self.state.player:
                        died_from_rad = self.state.player.take_radiation(rad_gain)
                        if rad_gain > 0:
                            print(f"[!] You absorbed {rad_gain} rads from the environment.")
                        if died_from_rad:
                            print("\nYour body succumbs to the radiation. You have become a puddle of goo.")
                            self.running = False
                            return

            # Check for random encounter
            if self._check_random_encounter():
                return
                
            # Check for enemies in new location
            self._check_location_enemies(destination_id)
        else:
            print(f"You can't go {direction} from here.")
    
    def _check_random_encounter(self) -> bool:
        """Check for random encounter during travel"""
        # 20% chance of encounter
        if random.random() < 0.2:
            enemies = ['radroach', 'mongrel', 'raider_scum']
            # Higher level enemies for dangerous areas could be added here
            
            enemy_key = random.choice(enemies)
            enemy = create_enemy(enemy_key)
            
            if enemy:
                print("\nSomething blocks your path...")
                self._start_combat(enemy)
                return True
        return False
        
    def _check_location_enemies(self, location_id: str):
        """Check for enemies in the location"""
        location = self.location_manager.get_location(location_id)
        if not location or not location.enemies:
            return
            
        # Get the first enemy
        # In a more complex system, you might have multiple enemies or a choice
        enemy = location.enemies[0]
        
        # Only aggressive enemies attack automatically
        # For now, assume all enemies in location.enemies are hostile
        if location.get_property('hostile', False) or enemy.name == 'Feral Ghoul':
            print(f"\nAs you enter {location.name}, you spot a threat!")
            self._start_combat(enemy)
    
    def _show_inventory(self):
        """Show player inventory"""
        if self.state.inventory:
            print(self.state.inventory.display())
        else:
            print("Inventory is empty.")
    
    def _show_stats(self):
        """Show player stats"""
        if self.state.player:
            print(self.state.player.get_stat_summary())
            print(f"Faction Reputation:")
            for faction, rep in self.state.faction_reputation.items():
                standing = self.state.get_faction_standing(faction)
                print(f"  {faction}: {standing} ({rep})")
    
    def _handle_look(self, args: List[str]):
        """Handle look/examine command"""
        if not args:
            # Look at current location
            location = self.location_manager.get_location(self.state.current_location)
            if location:
                print(location.get_description(detailed=True))
            return

        target = ' '.join(args).lower()
        
        # Check inventory
        if self.state.inventory:
            item = self.state.inventory.find_item(target)
            if item:
                print(f"\n[{item.name}]")
                print(item.description)
                print(f"Weight: {item.weight} | Value: {item.value}")
                if hasattr(item, 'damage'):
                    print(f"Damage: {item.damage} | Type: {item.weapon_type} | Skill: {item.skill}")
                elif hasattr(item, 'damage_resistance'):
                    print(f"Damage Resistance: {item.damage_resistance}")
                return

        # Check location
        location = self.location_manager.get_location(self.state.current_location)
        if location:
            # Check items on ground
            item = location.find_item(target)
            if item:
                print(f"\n[{item.name} (on the ground)]")
                print(item.description)
                return
            
            # Check enemies
            enemy = location.find_enemy(target)
            if enemy:
                print(f"\n[{enemy.name}]")
                print(enemy.description)
                print(f"Level: {enemy.level} | HP: {enemy.hp}/{enemy.max_hp}")
                return
            
            # Check for NPCs or features (simplified)
            if target in [npc.lower() for npc in location.npcs]:
                print(f"\nYou see {target}. Maybe you should 'talk' to them.")
                return

        print(f"You don't see any '{target}' here.")
    
    def _handle_take(self, args: List[str]):
        """Handle take/get command"""
        if not args:
            print("Take what?")
            return
        
        item_name = ' '.join(args)
        location = self.location_manager.get_location(self.state.current_location)
        if not location:
            return
        
        item = location.remove_item(item_name)
        if item:
            if self.state.inventory.add_item(item):
                print(f"You take the {item.name}.")
                self._sync_location_state()
            else:
                location.add_item(item)  # Put it back
                print("You can't carry that. Your inventory is too full.")
        else:
            print(f"You don't see {item_name} here.")
    
    def _handle_use(self, args: List[str]):
        """Handle use command"""
        if not args:
            print("Use what?")
            return
        
        item_name = ' '.join(args)
        item = self.state.inventory.find_item(item_name) if self.state.inventory else None
        
        if not item:
            print(f"You don't have {item_name}.")
            return
        
        if item.item_type == 'consumable':
            self._use_consumable(item)
        else:
            print(f"You can't use {item.name} like that.")
    
    def _use_consumable(self, item):
        """Use a consumable item"""
        from fallout_berlin.item import Consumable
        if not isinstance(item, Consumable):
            return
        
        if not self.state.player:
            return
        
        if item.effect_type == 'heal':
            self.state.player.heal(item.effect_value)
            print(f"You use {item.name} and restore {item.effect_value} HP.")
        elif item.effect_type == 'rad_heal':
            self.state.player.cure_radiation(item.effect_value)
            print(f"You use {item.name} and remove {item.effect_value} radiation.")
        
        self.state.inventory.remove_item(item.name, 1)
    
    def _handle_talk(self, args: List[str]):
        """Handle talk command"""
        if not args:
            print("Talk to whom?")
            return
        
        npc_name = ' '.join(args).lower()
        
        # Example: Hans at checkpoint charlie
        if ('hans' in npc_name or 'trader' in npc_name) and self.state.current_location == 'checkpoint_charlie':
            # Complete quest objective if player talks to Hans
            if "first_steps" in self.state.quests:
                self.quest_manager.complete_objective("first_steps", "talk_hans")
            self._start_dialogue('trader_charlie')
        else:
            print(f"You don't see {npc_name} here.")
    
    def _start_dialogue(self, npc_id: str):
        """Start dialogue with an NPC"""
        tree = self.dialogue_manager.get_dialogue_tree(npc_id)
        if not tree:
            print("That person doesn't want to talk.")
            return
        
        self.in_dialogue = True
        self.current_dialogue_tree = tree
        self.current_dialogue_node = tree.get_start_node()
        self._display_dialogue_node()
    
    def _display_dialogue_node(self):
        """Display current dialogue node"""
        if not self.current_dialogue_node:
            self.in_dialogue = False
            return
        
        node = self.current_dialogue_node
        speaker = self.current_dialogue_tree.npc_name if node.speaker != 'player' else 'You'
        
        print(f"\n{speaker}: {node.text}\n")
        
        options = node.get_available_options(self.state)
        if options:
            for i, option in enumerate(options, 1):
                print(f"{i}. {option.text}")
        else:
            print("(No options available)")
            self.in_dialogue = False
    
    def _handle_dialogue_command(self, command: str):
        """Handle commands during dialogue"""
        node = self.current_dialogue_node
        if not node:
            self.in_dialogue = False
            return
        
        options = node.get_available_options(self.state)
        
        try:
            choice = int(command)
            if 1 <= choice <= len(options):
                option = options[choice - 1]
                
                # Check for faction info quest objective
                if option.next_node == "factions" and "first_steps" in self.state.quests:
                    self.quest_manager.complete_objective("first_steps", "learn_factions")
                
                # Execute action if any
                if option.action:
                    option.action(self.state)
                
                # Move to next node
                if option.next_node:
                    next_node = self.current_dialogue_tree.get_node(option.next_node)
                    self.current_dialogue_node = next_node
                    self._display_dialogue_node()
                elif option.end_dialogue or not option.next_node:
                    self.in_dialogue = False
                    print("\n[End of conversation]")
            else:
                print("Invalid choice.")
        except ValueError:
            if command in ['exit', 'leave', 'bye']:
                self.in_dialogue = False
                print("\n[You end the conversation]")
            else:
                print("Please enter a number or 'exit' to leave.")
    
    def _show_quests(self):
        """Show quest log"""
        print(self.quest_manager.get_quests_display(self.state))
    
    def _show_help(self):
        """Show help menu"""
        print("""
=== COMMANDS ===

Movement:
  go [direction], north/south/east/west, n/s/e/w
  - Move to a connected location

Interaction:
  look, examine [target] - Look around or at something
  take [item] - Pick up an item
  use [item] - Use a consumable item
  equip, wear, wield [item] - Equip weapon or armor
  craft [recipe_id] - Craft an item
  talk [npc] - Talk to an NPC

Information:
  inventory, inv, i - View inventory
  stats, character - View character stats
  quest, quests, q - View quest log

Game:
  save - Save game
  load - Load game
  help - Show this help
  quit, exit - Quit game

During dialogue, enter the number of your choice.
        """)
    
    def _save_game(self):
        """Save the game"""
        filename = input("Save filename (default: savegame.json): ").strip()
        if not filename:
            filename = "savegame.json"
        if not filename.endswith('.json'):
            filename += '.json'
        
        filepath = self.state.save_game(filename)
        print(f"Game saved to {filepath}")
    
    def _save_game_prompt(self):
        """Prompt to save before quitting"""
        response = input("Save before quitting? (y/n): ").strip().lower()
        if response == 'y':
            self._save_game()
    
    def _load_game(self):
        """Load a game"""
        saves = self.state.list_saves()
        if not saves:
            print("No save games found.")
            return
        
        print("\nAvailable saves:")
        for i, save in enumerate(saves, 1):
            print(f"{i}. {save['filename']} - {save['date']} - {save['location']}")
        
        try:
            choice = input("\nEnter save number: ").strip()
            choice_num = int(choice)
            if 1 <= choice_num <= len(saves):
                filename = saves[choice_num - 1]['filename']
                if self.state.load_game(filename):
                    print(f"Game loaded from {filename}")
                    # Update managers with loaded state
                    self.quest_manager.quests = self.state.quests
                    self.running = True
                else:
                    print("Failed to load game.")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a number.")
    
    def _quit_game(self):
        """Quit the game"""
        self._save_game_prompt()
        print("\nThanks for playing Fallout: Berlin!")
        self.running = False
        sys.exit(0)


def main():
    """Main entry point"""
    engine = GameEngine()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--load' and len(sys.argv) > 2:
            # Load specific save
            if engine.state.load_game(sys.argv[2]):
                engine.running = True
                engine.game_loop()
            else:
                print("Failed to load game.")
        else:
            print("Usage: python -m fallout_berlin.game_engine [--load <savefile>]")
    else:
        # Start new game or show menu
        print("\n1. New Game")
        print("2. Load Game")
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            engine.start_new_game()
        elif choice == '2':
            engine._load_game()
            if engine.running:
                engine.game_loop()
        else:
            print("Invalid choice.")


if __name__ == '__main__':
    main()
