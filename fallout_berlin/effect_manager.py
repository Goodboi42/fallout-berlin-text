from typing import TYPE_CHECKING
from colorama import Fore, Style
from fallout_berlin.item import Consumable

if TYPE_CHECKING:
    from fallout_berlin.player import Player
    from fallout_berlin.inventory import Inventory

class EffectManager:
    """
    Handles the application of effects from consumables and other sources.
    Externalizes logic from GameEngine.
    """

    def apply_effect(self, item: Consumable, player: 'Player', inventory: 'Inventory') -> bool:
        """
        Apply the effect of a consumable item to the player.
        Returns True if the item was successfully used.
        """
        if not isinstance(item, Consumable):
            return False

        used = False

        if item.effect_type in {"heal", "heal_major", "heal_buff_faction", "heal_rads"}:
            base_heal = item.effect_value
            if player.has_perk("Medic"):
                bonus = int(base_heal * 0.5)
                total_heal = base_heal + bonus
                previous_hp = player.hit_points
                player.heal(total_heal)
                healed = player.hit_points - previous_hp
                print(f"You use {item.name} and restore {Fore.GREEN}{healed} HP (Medic bonus included){Style.RESET_ALL}.")
            else:
                previous_hp = player.hit_points
                player.heal(base_heal)
                healed = player.hit_points - previous_hp
                print(f"You use {item.name} and restore {Fore.GREEN}{healed} HP{Style.RESET_ALL}.")
            used = True

        elif item.effect_type == "rad_heal":
            player.cure_radiation(item.effect_value)
            print(f"You use {item.name} and remove {Fore.GREEN}{item.effect_value} radiation{Style.RESET_ALL}.")
            used = True

        elif item.effect_type == "fatigue_heal":
            player.fatigue = max(0, player.fatigue - item.effect_value)
            print(f"You consume {item.name}. {Fore.GREEN}You feel energized.{Style.RESET_ALL}")
            used = True

        elif item.effect_type == "rad_resist":
            # For now, we apply it as a flat bonus to radiation_resistance.
            # In a full implementation, this should be timed.
            player.radiation_resistance += item.effect_value
            print(f"You use {item.name}. Radiation resistance increased by {Fore.GREEN}{item.effect_value}%{Style.RESET_ALL}.")
            used = True

        elif item.effect_type == "food":
            player.update_survival_stats(hunger_inc=-item.effect_value)
            print(f"You eat {item.name}. {Fore.GREEN}Hunger reduced.{Style.RESET_ALL}")
            used = True

        elif item.effect_type == "drink":
            player.update_survival_stats(thirst_inc=-item.effect_value)
            print(f"You drink {item.name}. {Fore.GREEN}Thirst reduced.{Style.RESET_ALL}")
            used = True

        elif item.effect_type == "buff_perception_cold_resist":
            player.base_special["perception"] += item.effect_value
            player._recalculate_stats()
            print(f"You use {item.name}. {Fore.GREEN}Perception increased by {item.effect_value}.{Style.RESET_ALL}")
            used = True

        # Handle radiation damage from food/drink
        radiation_damage = getattr(item, "radiation_damage", 0)
        if radiation_damage > 0:
            previous_radiation = player.radiation
            is_food = item.effect_type in {"food", "food_random_effect", "heal_rads"}
            player.take_radiation(radiation_damage, from_food=is_food)
            actual_radiation = player.radiation - previous_radiation
            if actual_radiation:
                print(f"{Fore.RED}The {item.name} was irradiated! (+{actual_radiation} Rads){Style.RESET_ALL}")
            elif is_food and player.has_perk("Lead Belly"):
                print(f"{Fore.GREEN}Lead Belly prevents radiation from {item.name}.{Style.RESET_ALL}")
            used = True # If it had rads, it was consumed

        if used:
            inventory.remove_item(item.name, 1)
            return True

        print(f"{Fore.YELLOW}{item.name} has no implemented effect yet.{Style.RESET_ALL}")
        return False

