import random
from typing import Tuple, Any, Dict, Optional
from colorama import Fore, Style
from fallout_berlin.item import Consumable

class CombatManager:
    ATTACK_AP_COST = 5

    def __init__(self, state, location_manager, ui_manager):
        self.state = state
        self.location_manager = location_manager
        self.ui_manager = ui_manager
        self.current_enemy = None
        self.in_combat = False   # B9 fix: explicitly declared
        self.in_vats = False
        self.last_action_feedback = ""
        self._victory_processed = False

    def start_combat(self, enemy):
        self.current_enemy = enemy
        self.in_combat = True
        self.in_vats = False
        self._victory_processed = False
        self.last_action_feedback = f"Combat started with {enemy.name}!"

        # Initialize AP if missing
        player = self.state.player
        if not hasattr(player, 'max_ap'):
            player.max_ap = 10 + getattr(player, 'agility', 5)
        if not hasattr(player, 'current_ap'):
            player.current_ap = player.max_ap


    def process_combat_turn(self, command: str, engine) -> Tuple[str, Any]:
        player = self.state.player
        enemy = self.current_enemy

        if enemy is None:
            self._end_combat(player)
            return "ESCAPED", None

        if enemy.hp <= 0:
            return self._complete_victory(player, enemy)

        # Player Action
        action_result = self._handle_player_action(command, player, enemy, engine)

        if action_result == "fled":
            self._end_combat(player)
            return "ESCAPED", None

        if enemy.hp <= 0:
            return self._complete_victory(player, enemy)

        # Companion turn — fires after any valid player action
        if action_result != "invalid":
            companion = getattr(self.state, "companion", None)
            if companion and getattr(companion, "is_alive", False) and companion.hp > 0:
                companion_dmg = companion.attack()
                enemy.take_damage(companion_dmg)
                self.last_action_feedback += (
                    f"\n{Fore.CYAN}{companion.name} attacks {enemy.name} for {companion_dmg} damage!{Style.RESET_ALL}"
                )

            if enemy.hp <= 0:
                return self._complete_victory(player, enemy)

            # Enemy Turn (only if player didn't flee and enemy is alive)
            self._handle_enemy_turn(player, enemy)

        if player.hit_points <= 0:
            self._end_combat(player)
            return "DEFEAT", None

        return "CONTINUE", None

    def _end_combat(self, player):
        self.in_combat = False
        self.in_vats = False
        player.reset_ap()

    def _complete_victory(self, player, enemy):
        if not self._victory_processed:
            self._victory_processed = True
            location = (
                self.location_manager.get_location(self.state.current_location)
                if self.location_manager
                else None
            )
            if location and enemy in location.enemies:
                location.enemies.remove(enemy)

            experience = max(0, getattr(enemy, "xp_reward", 0))
            if experience:
                player.add_experience(experience)

            enemy_id = getattr(enemy, "enemy_id", "")
            killed_creatures = getattr(self.state, "killed_creatures", None)
            if enemy_id and isinstance(killed_creatures, dict):
                killed_creatures[enemy_id] = killed_creatures.get(enemy_id, 0) + 1

            reward_message = f" You earned {experience} XP." if experience else ""
            self.last_action_feedback += (
                f"\n{Fore.GREEN}You defeated {enemy.name}!{reward_message}{Style.RESET_ALL}"
            )
        self._end_combat(player)
        return "VICTORY", enemy.get_loot()

    def _handle_player_action(self, command: str, player, enemy, engine) -> str:
        self.last_action_feedback = ""

        if command in ["end turn", "wait"]:
            self.last_action_feedback = "You end your turn and recover action points."
            return "end_turn"
        
        if command == "attack":
            return self._perform_attack(player, enemy, "Torso")
        
        if command.startswith("vats "):
            part = command[5:].strip()
            return self._perform_attack(player, enemy, part, use_ap=True)

        if command == "heal":
            item = self.state.inventory.find_item("stimpak")
            effect_manager = getattr(engine, "effect_manager", None)
            if isinstance(item, Consumable) and effect_manager:
                previous_hp = player.hit_points
                if effect_manager.apply_effect(item, player, self.state.inventory):
                    healed = player.hit_points - previous_hp
                    self.last_action_feedback = f"{Fore.GREEN}Used {item.name}. Healed {healed} HP.{Style.RESET_ALL}"
                    return "heal"
            self.last_action_feedback = f"{Fore.RED}No usable Stimpaks remaining!{Style.RESET_ALL}"
            return "invalid"

        if command == "flee":
            # Chance based on Agility vs Enemy Level
            escape_chance = 0.4 + (player.agility * 0.05)
            if random.random() < escape_chance:
                self.last_action_feedback = f"{Fore.GREEN}You managed to escape!{Style.RESET_ALL}"
                return "fled"
            else:
                self.last_action_feedback = f"{Fore.RED}Failed to escape!{Style.RESET_ALL}"
                return "failed_flee"
        
        if command == "take cover":
             player.defense_bonus = 5
             self.last_action_feedback = f"{Fore.YELLOW}You take cover, increasing defense.{Style.RESET_ALL}"
             return "cover"

        # Handle equip/use from global commands passed down
        if command.startswith("equip "):
             item_name = command[6:].strip()
             item = self.state.inventory.find_item(item_name)
             if item and player.equip_item(item):
                 self.last_action_feedback = f"{Fore.GREEN}Equipped {item.name}.{Style.RESET_ALL}"
                 return "equip"
             self.last_action_feedback = f"{Fore.RED}Cannot equip that.{Style.RESET_ALL}"
             return "invalid"

        if command.startswith("use "):
            item_name = command[4:].strip()
            item = self.state.inventory.find_item(item_name)
            effect_manager = getattr(engine, "effect_manager", None)
            if isinstance(item, Consumable) and effect_manager:
                if effect_manager.apply_effect(item, player, self.state.inventory):
                    self.last_action_feedback = f"{Fore.GREEN}Used {item.name}.{Style.RESET_ALL}"
                    return "use"
            self.last_action_feedback = f"{Fore.RED}Cannot use that item.{Style.RESET_ALL}"
            return "invalid"

        self.last_action_feedback = f"{Fore.YELLOW}Unknown combat command.{Style.RESET_ALL}"
        return "invalid"

    def _perform_attack(self, player, enemy, target_part="Torso", use_ap=False):
        if use_ap and not player.spend_ap(self.ATTACK_AP_COST):
            self.last_action_feedback = f"{Fore.YELLOW}Not enough AP to attack (cost: {self.ATTACK_AP_COST}).{Style.RESET_ALL}"
            return "invalid"

        target_part = next(
            (
                part
                for part in self.get_vats_chances()
                if part.casefold() == target_part.casefold()
            ),
            "Torso",
        )
        weapon = player.equipped_weapon
        damage = weapon.damage if weapon else player.strength // 2
        
        # Calculate Hit Chance
        chances = self.get_vats_chances()
        hit_chance = chances.get(target_part, 50)
        
        if random.randint(1, 100) <= hit_chance:
            # Critical Logic
            crit_mult = 1.0
            if target_part == "Head": 
                damage = int(damage * 1.5)
                crit_mult = 1.5
            
            # Defense Mitigation
            previous_hp = enemy.hp
            enemy.take_damage(damage)
            actual_damage = previous_hp - enemy.hp
            
            part_msg = f" in the {target_part}" if target_part != "Torso" else ""
            crit_msg = " (CRITICAL)" if crit_mult > 1.0 else ""
            
            self.last_action_feedback = f"{Fore.GREEN}You hit {enemy.name}{part_msg} for {actual_damage} damage!{crit_msg}{Style.RESET_ALL}"
        else:
            self.last_action_feedback = f"{Fore.RED}You missed {enemy.name}!{Style.RESET_ALL}"
            
        return "attack"

    def _handle_enemy_turn(self, player, enemy):
        attack_damage = enemy.get_attack_damage()
        attack_damage = max(1, attack_damage - getattr(player, 'defense_bonus', 0))
        if getattr(player, 'god_mode', False):
            self.last_action_feedback += f"\n{Fore.YELLOW}{enemy.name} attacks, but you are invincible!{Style.RESET_ALL}"
        else:
            damage = player.take_damage(attack_damage)
            self.last_action_feedback += f"\n{Fore.RED}{enemy.name} attacks you for {damage} damage!{Style.RESET_ALL}"

        player.defense_bonus = 0
        
        # Regenerate AP
        if hasattr(player, 'max_ap') and hasattr(player, 'current_ap'):
            regen = 2 + (getattr(player, 'agility', 5) // 2)
            player.current_ap = min(player.max_ap, player.current_ap + int(regen))

    def get_vats_chances(self) -> Dict[str, int]:
        """Calculate hit chances for VATS based on stats"""
        player = self.state.player
        # Base accuracy derived from Perception and Agility
        base = 50 + (player.perception * 4) + (player.agility * 2)
        
        # Body part modifiers
        return {
            "Head": min(95, max(0, base - 30)),
            "Torso": min(95, max(0, base + 10)),
            "Left Arm": min(95, max(0, base - 10)),
            "Right Arm": min(95, max(0, base - 10)),
            "Left Leg": min(95, max(0, base - 10)),
            "Right Leg": min(95, max(0, base - 10)),
        }