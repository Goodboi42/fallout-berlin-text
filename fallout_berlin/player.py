"""
Player Character System
Handles S.P.E.C.I.A.L. stats, skills, and character creation
"""

from typing import Dict, Any, Optional, List
import random


class Player:
    """Player character with S.P.E.C.I.A.L. stats and skills"""

    # Skill list based on Fallout
    SKILLS = [
        "Small Guns",
        "Big Guns",
        "Energy Weapons",
        "Unarmed",
        "Melee Weapons",
        "Throwing",
        "First Aid",
        "Doctor",
        "Sneak",
        "Lockpick",
        "Steal",
        "Traps",
        "Science",
        "Repair",
        "Speech",
        "Barter",
        "Gambling",
        "Outdoorsman",
    ]

    # Origins for character creation
    ORIGINS = {
        "vault_dweller": {
            "name": "Vault 17 Survivor",
            "description": "You grew up in Vault 17-Berlin, hidden beneath the Brandenburg Gate.",
            "bonuses": {"Science": 15, "Repair": 10, "First Aid": 10},
            "starting_items": ["Vault Suit", "Pip-Boy", "Stimpak x3", "Atom-Cola x2", "Mutated Fruit x2"],
        },
        "wastelander": {
            "name": "Kiez Survivor",
            "description": "You survived the streets of Neukölln and Kreuzberg, learning to adapt to the chaos.",
            "bonuses": {"Outdoorsman": 15, "Sneak": 10, "First Aid": 10},
            "starting_items": ["Leather Armor", "10mm Pistol", "RadAway x2"],
        },
        "ghoul": {
            "name": "Charité Remnant",
            "description": "A former medical researcher at the Charité who was too close to the blast. You have seen centuries of Berlin history.",
            "bonuses": {"Radiation Resistance": 50, "Outdoorsman": 10},
            "starting_items": ["Tattered Clothes", "Pipe Pistol", "RadAway x5"],
            "special": "Radiation immunity, long lifespan, some prejudice",
        },
        "raider": {
            "name": "U-Bahn Raider",
            "description": "You were part of the Tunnel Rats, a gang that controls the U1 line.",
            "bonuses": {"Small Guns": 15, "Melee Weapons": 10, "Sneak": 10},
            "starting_items": ["Raider Armor", "10mm Pistol", "Knife"],
        },
        "trader": {
            "name": "Späti Mogul",
            "description": "Your family ran the most successful underground trade network in the Mitte Ruins.",
            "bonuses": {"Barter": 20, "Speech": 15, "Outdoorsman": 10},
            "starting_items": [
                "Leather Armor",
                "Pipe Pistol",
                "Caps x200",
                "Späti Token",
            ],
        },
        "scientist": {
            "name": "Siemens Technician",
            "description": "A descendant of the engineers who tried to keep Berlin\'s power grid alive.",
            "bonuses": {"Science": 20, "Repair": 15, "Doctor": 10},
            "starting_items": ["Lab Coat", "Tool Kit", "Stimpak x2"],
        },
    }

    def __init__(self, name: str = "Player"):
        self.name = name
        self.origin = None

        # S.P.E.C.I.A.L. stats (1-10 each, start at 5)
        self.strength = 5
        self.perception = 5
        self.endurance = 5
        self.charisma = 5
        self.intelligence = 5
        self.agility = 5
        self.luck = 5

        # Base stats for recalculation
        self.base_special = {
            "strength": 5,
            "perception": 5,
            "endurance": 5,
            "charisma": 5,
            "intelligence": 5,
            "agility": 5,
            "luck": 5,
        }

        # Skills (0-200, start at base values)
        self.skills = {
            skill: self._calculate_base_skill(skill) for skill in self.SKILLS
        }

        # Derived stats
        self.hit_points = 0
        self.max_hit_points = 0
        self.radiation = 0
        self.max_radiation = 1000 # Reworked: 1000 is always fatal
        self.radiation_resistance = 0
        self.base_rad_resistance = 0
        self.max_ap = 0
        self.current_ap = 0
        self.carry_weight = 0

        # Survival Stats (0-100)
        self.hunger = 0
        self.thirst = 0
        self.fatigue = 0

        # Equipment
        from fallout_berlin.item import Weapon, Armor

        self.equipped_weapon: Optional[Weapon] = None
        self.equipped_armor: Optional[Armor] = None

        # Status effects
        self.active_effects = [] # Changed from status_effects to active_effects and now a list of strings

        # Experience
        self.level = 1
        self.experience = 0
        self.experience_to_next = 1000

        self.stat_points = 0
        self.perks = []
        self.is_sneaking = False
        # Starting items will be added during creation
        self._calculate_derived_stats()
        self.is_alive = True
        self.properties = {}

    def get_property(self, key: str, default: Any = None) -> Any:
        """Get a custom property"""
        return self.properties.get(key, default)

    def set_property(self, key: str, value: Any):
        """Set a custom property"""
        self.properties[key] = value

    def update_survival_stats(self, hunger_inc=0, thirst_inc=0, fatigue_inc=0, minutes=1):
        """Update survival stats and check for penalties"""
        self.hunger = min(100, max(0, self.hunger + hunger_inc))
        self.thirst = min(100, max(0, self.thirst + thirst_inc))
        self.fatigue = min(100, max(0, self.fatigue + fatigue_inc))

        self._recalculate_stats()
        # Handle time-based effects
        self.tick_game_time(minutes)

        # Return True if taking damage
        if self.hunger >= 100 or self.thirst >= 100:
            return self.take_damage(5)  # Starvation/Dehydration damage
        return False

    def _recalculate_stats(self):
        """Reset stats to base and apply penalties"""
        for stat, value in self.base_special.items():
            setattr(self, stat, value)

        # Perk: Solar Powered (+2 STR during day)
        if self.has_perk("Solar Powered"):
            if self.get_property("is_outside", False) and 6 <= self.get_property("game_hour", 12) <= 18:
                self.strength = min(10, self.strength + 2)

        self._apply_survival_penalties()
        self._apply_radiation_penalties()
        self._calculate_derived_stats()
        self._recalculate_skills()

    def _apply_radiation_penalties(self):
        """Apply S.P.E.C.I.A.L. penalties from radiation sickness"""
        penalties = self.get_radiation_sickness_effects()
        for stat, penalty in penalties.items():
            current_val = getattr(self, stat)
            setattr(self, stat, max(1, current_val + penalty))

    def is_overencumbered(self, current_weight: float) -> bool:
        """Check if player is carrying too much"""
        return current_weight > self.carry_weight

    def _apply_survival_penalties(self):
        """Apply S.P.E.C.I.A.L. penalties based on survival stats"""
        # Hunger
        if self.hunger >= 80:
            self.strength = max(1, self.strength - 2)
            self.endurance = max(1, self.endurance - 2)
            self.agility = max(1, self.agility - 1)
        elif self.hunger >= 50:
            self.strength = max(1, self.strength - 1)
            self.endurance = max(1, self.endurance - 1)

        # Thirst
        if self.thirst >= 80:
            self.perception = max(1, self.perception - 2)
            self.intelligence = max(1, self.intelligence - 2)
            self.luck = max(1, self.luck - 1)
        elif self.thirst >= 50:
            self.perception = max(1, self.perception - 1)
            self.intelligence = max(1, self.intelligence - 1)

        # Fatigue
        if self.fatigue >= 80:
            self.agility = max(1, self.agility - 2)
            self.strength = max(1, self.strength - 1)
        elif self.fatigue >= 50:
            self.agility = max(1, self.agility - 1)

    def get_survival_status(self) -> str:
        """Get description of survival status"""
        status = []
        if self.hunger > 80:
            status.append("Starving")
        elif self.hunger > 50:
            status.append("Hungry")

        if self.thirst > 80:
            status.append("Dehydrated")
        elif self.thirst > 50:
            status.append("Thirsty")

        if self.fatigue > 80:
            status.append("Exhausted")
        elif self.fatigue > 50:
            status.append("Tired")

        return ", ".join(status) if status else "Healthy"

    def _calculate_base_skill(self, skill: str) -> int:
        """Calculate base skill value from S.P.E.C.I.A.L."""
        skill_map = {
            "Small Guns": "agility",
            "Big Guns": "strength",
            "Energy Weapons": "perception",
            "Unarmed": "strength",
            "Melee Weapons": "strength",
            "Throwing": "agility",
            "First Aid": "intelligence",
            "Doctor": "intelligence",
            "Sneak": "agility",
            "Lockpick": "perception",
            "Steal": "agility",
            "Traps": "perception",
            "Science": "intelligence",
            "Repair": "intelligence",
            "Speech": "charisma",
            "Barter": "charisma",
            "Gambling": "luck",
            "Outdoorsman": "endurance",
        }

        primary_stat = getattr(self, skill_map.get(skill, "intelligence"))
        return primary_stat * 2 + 5

    def get_effective_max_hp(self) -> int:
        """Calculate Max HP reduced by radiation (10 Rads = -1% Max HP)"""
        reduction_percent = self.radiation / 1000.0
        effective_max = int(self.max_hit_points * (1.0 - reduction_percent))
        return max(0, effective_max)

    def get_radiation_sickness_effects(self) -> Dict[str, int]:
        """Calculate S.P.E.C.I.A.L. penalties based on radiation level"""
        penalties = {}
        rads = self.radiation
        
        if rads >= 800: # Critical
            penalties = {"endurance": -3, "agility": -2, "strength": -2, "luck": -1}
        elif rads >= 600: # Severe
            penalties = {"endurance": -3, "agility": -2, "strength": -1}
        elif rads >= 400: # Advanced
            penalties = {"endurance": -2, "agility": -1}
        elif rads >= 200: # Minor
            penalties = {"endurance": -1}
            
        return penalties

    def _calculate_derived_stats(self):
        """Calculate derived stats from S.P.E.C.I.A.L. and Perks"""
        # Hit Points = 25 + (Endurance * 2) + (Level * 2)
        # We use base_special endurance here because current endurance might have penalties
        self.max_hit_points = 25 + (self.base_special["endurance"] * 2) + (self.level * 2)

        # Apply Perk: Lifegiver
        if self.has_perk("Lifegiver"):
            self.max_hit_points += 20
        
        # Ensure current HP doesn't exceed effective max HP
        effective_max = self.get_effective_max_hp()
        if self.hit_points == 0:
            self.hit_points = effective_max
        else:
            self.hit_points = min(self.hit_points, effective_max)

        # Max Radiation is 1000 for everyone in this system
        self.max_radiation = 1000

        # Radiation Resistance
        self.radiation_resistance = self.base_rad_resistance
        if self.has_perk("Rad Resistant"):
            self.radiation_resistance += 15
        
        # Origin Ghoul check (if not already handled in base_rad_resistance)
        if self.origin == "ghoul":
            self.radiation_resistance = max(self.radiation_resistance, 50)

        # Action Points = 5 + Agility
        self.max_ap = 5 + self.agility # Based on new design doc
        # If current_ap is not yet set or is 0, initialize it to max_ap
        if self.current_ap == 0 or self.current_ap > self.max_ap:
            self.current_ap = self.max_ap

        # Carry Weight = 25 + (Strength * 25)
        self.carry_weight = 25 + (self.strength * 25)

        # Apply Perk: Trümmerfrau
        if self.has_perk("Trümmerfrau"):
            self.carry_weight += 50

    def reset_ap(self):
        """Reset AP to max at start of combat or turn."""
        self.current_ap = self.max_ap

    def spend_ap(self, amount: int) -> bool:
        """Spend Action Points."""
        if self.current_ap >= amount:
            self.current_ap -= amount
            return True
        return False

    def add_ap(self, amount: int):
        """Add Action Points."""
        self.current_ap = min(self.max_ap, self.current_ap + amount)

    def regenerate_ap(self, amount: int = 0):
        """Regenerate Action Points based on Agility"""
        # Formula: 2 + (Agility / 2) per turn
        regen = amount if amount > 0 else (2 + (self.agility // 2))
        
        # Apply Stunned penalty (AP Regen reduced by 100%)
        if "Stunned" in self.active_effects:
            regen = 0
        # Apply Crippled Leg penalty (AP Regen reduced by 50%)
        elif any(k for k in self.active_effects if "Crippled Leg" in k):
            regen //= 2

        self.current_ap = min(
            self.max_ap, self.current_ap + regen
        )

    def set_origin(self, origin_key: str):
        """Set character origin and apply bonuses"""
        if origin_key not in self.ORIGINS:
            return False

        self.origin = origin_key
        origin_data = self.ORIGINS[origin_key]

        # Apply skill bonuses
        for skill, bonus in origin_data.get("bonuses", {}).items():
            if skill in self.skills:
                self.skills[skill] += bonus
            elif skill == "Radiation Resistance":
                self.base_rad_resistance += bonus

        return True

    def get_origin_data(self) -> Optional[Dict]:
        """Get origin data"""
        if self.origin:
            return self.ORIGINS[self.origin]
        return None

    def set_special(self, stat: str, value: int):
        """Set a S.P.E.C.I.A.L. stat (1-10)"""
        stat_key = stat.lower()
        if stat_key in self.base_special:
            self.base_special[stat_key] = max(1, min(10, value))
            self._recalculate_stats()

    def _recalculate_skills(self):
        """Recalculate skills based on current S.P.E.C.I.A.L."""
        for skill in self.SKILLS:
            base = self._calculate_base_skill(skill)
            # Preserve bonuses from origin
            if self.origin:
                origin_data = self.ORIGINS[self.origin]
                bonus = origin_data.get("bonuses", {}).get(skill, 0)
                self.skills[skill] = base + bonus
            else:
                self.skills[skill] = base

    def get_skill(self, skill: str) -> int:
        """Get skill value"""
        return self.skills.get(skill, 0)

    def modify_skill(self, skill: str, amount: int):
        """Modify skill value"""
        if skill in self.skills:
            self.skills[skill] = max(0, min(200, self.skills[skill] + amount))

    def get_skill_check_result(self, skill: str, difficulty: int = 50) -> bool:
        """Perform a skill check (returns True if successful)"""
        skill_value = self.get_skill(skill)
        # Roll 1-100, add skill value, compare to difficulty
        roll = random.randint(1, 100)
        total = roll + skill_value
        return total >= difficulty

    def take_damage(self, amount: int, enemy_dr: int = 0) -> int:
        """Take damage, factoring in Damage Resistance. Returns actual damage taken."""
        # Player DR = Armor_DR + (Endurance / 2)
        player_dr = (self.equipped_armor.damage_resistance if self.equipped_armor else 0) + (self.endurance // 2)
        
        # Apply crippled limb penalties to DR if any
        if "Crippled Torso" in self.active_effects: # Example for torso crippling effect
            player_dr = max(0, player_dr - 5) # Reduce DR by 5

        actual_damage = max(1, amount - player_dr)
        
        self.hit_points = max(0, self.hit_points - actual_damage)
        if self.hit_points <= 0:
            self.is_alive = False
        return actual_damage # Return actual damage taken

    def apply_status_effect(self, name: str):
        """Add or refresh a status effect (simplified for now to just a list of names)"""
        if name not in self.active_effects:
            self.active_effects.append(name)

    def remove_status_effect(self, name: str):
        """Remove a status effect"""
        if name in self.active_effects:
            self.active_effects.remove(name)

    def has_status_effect(self, name: str) -> bool:
        """Check if player has a specific status effect"""
        return name in self.active_effects

    def tick_status_effects(self):
        """Process status effects at end of turn (simplified)"""
        # In a full implementation, this would involve durations and more complex logic
        # For now, just a placeholder for potential future logic for player effects
        pass # Effects are currently primarily visual or handled directly in stat recalculations

    def get_hit_chance(self, weapon_type: str, enemy_cover_bonus: int = 0) -> int:
        """Calculate hit chance based on stats and weapon type"""
        # Skill lookup
        skill_name = "Small Guns" if weapon_type == "ranged" else "Melee Weapons"
        skill_value = self.get_skill(skill_name)
        
        if weapon_type == "ranged":
            # Hit Chance (Ranged): Skill_Value + (Perception * 2) + (Luck / 2) - Enemy_Cover_Bonus
            chance = skill_value + (self.perception * 2) + (self.luck // 2) - enemy_cover_bonus
            
            # Crippled Arm penalty: -30% with 2H, -15% with 1H (simplified to -20% here)
            if "Crippled Arm" in self.active_effects:
                chance = int(chance * 0.8)
            # Crippled Head penalty: -5 Perception (already factored if _recalculate_stats called,
            # but we can add an extra accuracy penalty here)
            if "Crippled Head" in self.active_effects:
                chance -= 15
        else:
            # Hit Chance (Melee): Skill_Value + (Strength * 2) + (self.agility // 2)
            chance = skill_value + (self.strength * 2) + (self.agility // 2)

        return max(5, min(95, chance)) # Cap between 5% and 95%

    def get_crit_chance(self) -> int:
        """Calculate critical hit chance"""
        # Crit Chance: (Luck * 1%) + Perk_Bonuses
        chance = self.luck
        if self.has_perk("Better Criticals"):
            chance += 5
        return chance

    def get_melee_damage_bonus(self) -> int:
        """Calculate melee damage bonus based on Strength"""
        # +1 damage for every point of Strength above 5
        return max(0, self.strength - 5)

    def heal(self, amount: int):
        """Heal damage (capped by radiation reduction)"""
        self.hit_points = min(self.get_effective_max_hp(), self.hit_points + amount)

    def take_radiation(self, amount: int, from_food: bool = False):
        """Take radiation damage (reduced by radiation resistance)"""
        # Perk: Lead Belly
        if from_food and self.has_perk("Lead Belly"):
            return False

        actual_rads = int(amount * (1.0 - (min(85, self.radiation_resistance) / 100.0)))
        
        # Perk: Ghoulish (Heal 1 HP per 10 Rads taken)
        if self.has_perk("Ghoulish") and actual_rads > 0:
            self.heal(actual_rads // 10)

        self.radiation = min(self.max_radiation, self.radiation + actual_rads)
        
        self._recalculate_stats()
        
        if self.radiation >= self.max_radiation:
            return True  # Death by radiation
        return False

    def has_perk(self, perk_name: str) -> bool:
        """Check if the player has a specific perk"""
        return any(p["name"] == perk_name for p in self.perks if isinstance(p, dict)) or \
               any(p == perk_name for p in self.perks if isinstance(p, str))

    def cure_radiation(self, amount: int):
        """Reduce radiation and update stats"""
        self.radiation = max(0, self.radiation - amount)
        self._recalculate_stats()

    def tick_game_time(self, minutes: int = 1):
        """Handle time-based effects (Perks, Status Effects)"""
        # Perk: Rad Absorption
        if self.has_perk("Rad Absorption"):
            self.cure_radiation(minutes)
        
        # Perk: Solar Powered (Health Regen and STR bonus handled in recalculate)
        if self.has_perk("Solar Powered"):
            # Check if it's day and outside (we need to know this from game state or engine)
            # For now, we'll check a property we can set
            if self.get_property("is_outside", False) and 6 <= self.get_property("game_hour", 12) <= 18:
                self.heal(minutes) # 1 HP per minute

    def add_experience(self, amount: int):
        """Add experience points"""
        self.experience += amount
        while self.experience >= self.experience_to_next:
            self.level_up()

    def level_up(self):
        """Level up the player"""
        self.experience -= self.experience_to_next
        self.level += 1
        self.stat_points += 1
        self.experience_to_next = int(self.experience_to_next * 1.5)
        self._calculate_derived_stats()
        # Full heal on level up
        self.hit_points = self.max_hit_points
        return True

    def equip_item(self, item: Any) -> bool:
        """Equip an item (weapon or armor)"""
        # Determine item type by checking attributes since imports might be circular
        if hasattr(item, 'damage'): # Weapon
            self.equipped_weapon = item
            return True
        elif hasattr(item, 'damage_resistance'): # Armor
            self.equipped_armor = item
            return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary for saving"""
        return {
            "name": self.name,
            "origin": self.origin,
            "strength": self.strength,
            "perception": self.perception,
            "endurance": self.endurance,
            "charisma": self.charisma,
            "intelligence": self.intelligence,
            "agility": self.agility,
            "luck": self.luck,
            "base_special": self.base_special,
            "skills": self.skills,
            "hit_points": self.hit_points,
            "max_hit_points": self.max_hit_points,
            "radiation": self.radiation,
            "max_radiation": self.max_radiation,
            "hunger": self.hunger,
            "thirst": self.thirst,
            "fatigue": self.fatigue,
            "level": self.level,
            "experience": self.experience,
            "experience_to_next": self.experience_to_next,
            "perks": self.perks,
            "stat_points": self.stat_points,
            "max_ap": self.max_ap,
            "current_ap": self.current_ap,
            "active_effects": self.active_effects, # Changed from status_effects
            "equipped_weapon": self.equipped_weapon.to_dict()
            if self.equipped_weapon
            else None,
            "equipped_armor": self.equipped_armor.to_dict()
            if self.equipped_armor
            else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Create player from dictionary"""
        from fallout_berlin.item import Weapon, Armor
        from fallout_berlin.inventory import Inventory # Import Inventory to properly initialize it

        player = cls(data.get("name", "Player"))
        player.origin = data.get("origin")
        player.strength = data.get("strength", 5)
        player.perception = data.get("perception", 5)
        player.endurance = data.get("endurance", 5)
        player.charisma = data.get("charisma", 5)
        player.intelligence = data.get("intelligence", 5)
        player.agility = data.get("agility", 5)
        player.luck = data.get("luck", 5)
        player.base_special = data.get("base_special", player.base_special)
        player.skills = data.get("skills", {})
        player.hit_points = data.get("hit_points", player.max_hit_points)
        player.max_hit_points = data.get("max_hit_points", player.max_hit_points)
        player.radiation = data.get("radiation", 0)
        player.max_radiation = data.get("max_radiation", player.max_radiation)
        player.hunger = data.get("hunger", 0)
        player.thirst = data.get("thirst", 0)
        player.fatigue = data.get("fatigue", 0)
        player.level = data.get("level", 1)
        player.experience = data.get("experience", 0)
        player.experience_to_next = data.get("experience_to_next", 1000)
        player.perks = data.get("perks", [])
        player.stat_points = data.get("stat_points", 0)
        player.max_ap = data.get("max_ap", 50)
        player.current_ap = data.get("current_ap", player.max_ap)
        player.active_effects = data.get("active_effects", []) # Changed from status_effects

        if data.get("equipped_weapon"):
            player.equipped_weapon = Weapon.from_dict(data["equipped_weapon"])
        if data.get("equipped_armor"):
            player.equipped_armor = Armor.from_dict(data["equipped_armor"])

        player._calculate_derived_stats()
        return player

    def get_stat_summary(self) -> str:
        """Get a summary of player stats"""
        penalties = self.get_radiation_sickness_effects()
        pen_str = ""
        if penalties:
            pen_str = "\nRadiation Sickness Penalties: " + ", ".join([f"{k.upper()} {v}" for k, v in penalties.items()])

        effective_max_hp = self.get_effective_max_hp()
        
        return f"""
=== {self.name} ===
Origin: {self.ORIGINS[self.origin]["name"] if self.origin else "None"}
Level: {self.level} | XP: {self.experience}/{self.experience_to_next}
Available Stat Points: {self.stat_points}{pen_str}

S.P.E.C.I.A.L.:
  Strength: {self.strength}     Perception: {self.perception}
  Endurance: {self.endurance}   Charisma: {self.charisma}
  Intelligence: {self.intelligence}  Agility: {self.agility}
  Luck: {self.luck}

Health: {self.hit_points}/{effective_max_hp} (Base: {self.max_hit_points}) HP
Action Points: {self.current_ap}/{self.max_ap}
Radiation: {self.radiation}/{self.max_radiation} rads (Res: {self.radiation_resistance}%)
Carry Weight: {self.carry_weight} lbs
"""
