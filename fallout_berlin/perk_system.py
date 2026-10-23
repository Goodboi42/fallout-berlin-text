import json
import os
import logging

class PerkEffect:
    """Represents a single mechanical effect of a perk or trait."""
    def __init__(self, effect_data):
        self.type = effect_data.get("type", "stat_mod")  # stat_mod, unlock_mechanic, dialogue_tag, etc.
        self.stat = effect_data.get("stat")
        self.value = effect_data.get("value")
        self.modifier = effect_data.get("modifier", "add")  # add, mult, set
        self.condition = effect_data.get("condition")
        self.mechanic = effect_data.get("mechanic")
        self.tag = effect_data.get("tag")

class Perk:
    """Represents a Perk or Trait definition."""
    def __init__(self, data):
        self.id = data.get("id")
        self.name = data.get("name")
        self.description = data.get("description")
        self.type = data.get("type", "perk")  # 'perk' or 'trait'
        self.requirements = data.get("requirements", [])
        self.effects = [PerkEffect(e) for e in data.get("effects", [])]

    def check_requirements(self, player):
        """
        Checks if a player meets the requirements for this perk.
        Assumes player object has 'stats' (SPECIAL dict) and 'level'.
        """
        for req in self.requirements:
            stat_name = req.get("stat").lower()
            req_value = req.get("value")
            op = req.get("op", ">=")

            player_val = 0
            if stat_name == "level":
                player_val = getattr(player, "level", 1)
            elif hasattr(player, "stats") and stat_name in player.stats:
                player_val = player.stats[stat_name]
            elif hasattr(player, "skills") and stat_name in player.skills:
                player_val = player.skills[stat_name]
            
            if op == ">=" and player_val < req_value:
                return False
            elif op == "<=" and player_val > req_value:
                return False
            elif op == "==" and player_val != req_value:
                return False
                
        return True

class PerkManager:
    """
    Manages the loading, acquisition, and effect calculation of perks and traits.
    """
    def __init__(self, data_file_path):
        self.perks = {}
        self.traits = {}
        self.load_data(data_file_path)

    def load_data(self, file_path):
        if not os.path.exists(file_path):
            logging.error(f"Perk data file not found: {file_path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            for p_data in data.get("perks", []):
                perk = Perk(p_data)
                self.perks[perk.id] = perk
                
            for t_data in data.get("traits", []):
                trait = Perk(t_data)
                trait.type = "trait"
                self.traits[trait.id] = trait
                
        except json.JSONDecodeError as e:
            logging.error(f"Failed to parse perk data: {e}")

    def get_available_perks(self, player):
        """Returns a list of Perk objects that the player can currently acquire."""
        available = []
        # Assuming player has a list or set of owned perk IDs
        owned_perks = getattr(player, "perks", [])
        
        for perk_id, perk in self.perks.items():
            if perk_id not in owned_perks:
                if perk.check_requirements(player):
                    available.append(perk)
        return available

    def get_available_traits(self):
        """Returns all traits (usually for character creation)."""
        return list(self.traits.values())

    def get_stat_modifier(self, player, stat_name):
        """
        Calculates the total modifier for a specific stat based on owned perks/traits.
        Returns a tuple (additive_mod, multiplier_mod).
        """
        additive = 0
        multiplier = 1.0
        
        owned_ids = getattr(player, "perks", [])
        # Combine perks and traits for lookup
        all_definitions = {**self.perks, **self.traits}

        for p_id in owned_ids:
            if p_id in all_definitions:
                perk = all_definitions[p_id]
                for effect in perk.effects:
                    if effect.type == "stat_mod" and effect.stat == stat_name:
                        if effect.modifier == "add":
                            additive += effect.value
                        elif effect.modifier == "mult":
                            multiplier += effect.value # e.g. +0.2 for 20%
                            
        return additive, multiplier

    def has_mechanic_unlock(self, player, mechanic_name):
        """Checks if the player has a perk that unlocks a specific mechanic."""
        owned_ids = getattr(player, "perks", [])
        all_definitions = {**self.perks, **self.traits}
        
        for p_id in owned_ids:
            if p_id in all_definitions:
                for effect in all_definitions[p_id].effects:
                    if effect.type == "unlock_mechanic" and effect.mechanic == mechanic_name:
                        return True
        return False

    def get_perk_by_id(self, perk_id):
        if perk_id in self.perks:
            return self.perks[perk_id]
        return self.traits.get(perk_id)