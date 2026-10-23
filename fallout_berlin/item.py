"""
Item System
Handles items, weapons, armor, and consumables.
"""
from typing import Dict, Any, Optional

class Item:
    def __init__(self, name: str, description: str, value: int = 0, weight: float = 0.0, item_type: str = "misc", item_id: str = ""):
        self.name = name
        self.description = description
        self.value = value
        self.weight = weight
        self.item_type = item_type
        self.item_id = item_id
        self.quantity = 1
        self.stackable = False

    def to_dict(self) -> Dict[str, Any]:
        data = {
            'class': self.__class__.__name__,
            'name': self.name,
            'description': self.description,
            'value': self.value,
            'weight': self.weight,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'quantity': self.quantity,
            'stackable': self.stackable
        }
        if hasattr(self, 'damage'): data['damage'] = self.damage
        if hasattr(self, 'weapon_type'): data['weapon_type'] = self.weapon_type
        if hasattr(self, 'skill'): data['skill'] = self.skill
        if hasattr(self, 'ammo_type'): data['ammo_type'] = self.ammo_type
        if hasattr(self, 'damage_resistance'): data['damage_resistance'] = self.damage_resistance
        if hasattr(self, 'armor_type'): data['armor_type'] = self.armor_type
        if hasattr(self, 'effect_type'): data['effect_type'] = self.effect_type
        if hasattr(self, 'effect_value'): data['effect_value'] = self.effect_value
        if hasattr(self, 'duration'): data['duration'] = self.duration
        if hasattr(self, 'radiation_damage'): data['radiation_damage'] = self.radiation_damage
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Item':
        class_name = data.get('class', 'Item')
        item = None
        
        description = data.get('description', 'No description available.')
        
        if class_name == 'Weapon':
            item = Weapon(
                data['name'], description, data.get('damage', 0),
                data.get('weapon_type', 'melee'), data.get('skill', 'Melee Weapons'),
                data.get('value', 0), data.get('weight', 0), data.get('ammo_type'),
                data.get('item_id', '')
            )
        elif class_name == 'Armor':
            item = Armor(
                data['name'], description, data.get('damage_resistance', 0),
                data.get('armor_type', 'body'), data.get('value', 0), data.get('weight', 0),
                data.get('item_id', '')
            )
        elif class_name == 'Consumable':
            item = Consumable(
                data['name'], description, data.get('effect_type', 'heal'),
                data.get('effect_value', 0), data.get('duration', 0),
                data.get('value', 0), data.get('weight', 0),
                data.get('item_id', '')
            )
        elif class_name == 'Ammo':
            item = Ammo(
                data['name'], description, data.get('quantity', 1),
                data.get('value', 0), data.get('weight', 0),
                data.get('item_id', '')
            )
        else:
            item = Item(
                data['name'], description, data.get('value', 0),
                data.get('weight', 0), data.get('item_type', 'misc'),
                data.get('item_id', '')
            )
            
        if item:
            item.quantity = data.get('quantity', 1)
            item.stackable = data.get('stackable', item.stackable)
            if 'radiation_damage' in data:
                item.radiation_damage = data['radiation_damage']
            
        return item
    
    def __str__(self):
        return self.name

class Weapon(Item):
    def __init__(self, name, description, damage, weapon_type, skill, value=0, weight=0, ammo_type=None, item_id=""):
        super().__init__(name, description, value, weight, "weapon", item_id)
        self.damage = damage
        self.weapon_type = weapon_type
        self.skill = skill
        self.ammo_type = ammo_type

class Armor(Item):
    def __init__(self, name, description, damage_resistance, armor_type, value=0, weight=0, item_id=""):
        super().__init__(name, description, value, weight, "armor", item_id)
        self.damage_resistance = damage_resistance
        self.armor_type = armor_type

class Consumable(Item):
    def __init__(self, name, description, effect_type, effect_value, duration=0, value=0, weight=0, item_id=""):
        super().__init__(name, description, value, weight, "consumable", item_id)
        self.effect_type = effect_type
        self.effect_value = effect_value
        self.duration = duration
        self.stackable = True

class Ammo(Item):
    def __init__(self, name, description, count=1, value=0, weight=0, item_id=""):
        super().__init__(name, description, value, weight, "ammo", item_id)
        self.quantity = count
        self.stackable = True

import json
import os

ITEM_JSON_DATABASE = {}

def load_item_database():
    """Load items from JSON data file"""
    global ITEM_JSON_DATABASE
    if ITEM_JSON_DATABASE:
        return

    data_path = os.path.join(os.path.dirname(__file__), 'data', 'items.json')
    if not os.path.exists(data_path):
        return
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            ITEM_JSON_DATABASE = json.load(f)
    except Exception as e:
        print(f"Error loading item database: {e}")

load_item_database()

ITEM_DATABASE = {
    "pistole_10mm": Weapon("10mm Pistole (Walther)", "A reliable, pre-war German sidearm. Stamped with 'Polizei Berlin'.", 18, "ranged", "Small Guns", 150, 3.5, "10mm_patronen"),
    "rohrpistole": Weapon("Rohrpistole (Pipe Pistol)", "Crude handgun fashioned from rusted plumbing and wood scraps.", 12, "ranged", "Small Guns", 30, 2.0, "10mm_patronen"),
    "rohrgewehr": Weapon("Rohrgewehr (Pipe Rifle)", "A long-barreled pipe weapon. Inaccurate but easy to repair.", 22, "ranged", "Small Guns", 50, 5.0, "10mm_patronen"),
    "kampfmesser": Weapon("Kampfmesser (Combat Knife)", "Standard issue Bundeswehr knife. The blade is stained but sharp.", 10, "melee", "Melee Weapons", 40, 1.0),
    "schlagstock": Weapon("Polizei Schlagstock", "A heavy rubber baton used by riot police.", 8, "melee", "Melee Weapons", 25, 2.0),
    "laser_mp": Weapon("Laser MP (Prototype)", "Experimental energy submachine gun found in Iron Ring bunkers.", 24, "ranged", "Energy Weapons", 350, 6.0, "fusionszellen"),
    "pipe_mauser": Weapon("Pipe Mauser", "A bolt-action rifle built to mimic historical designs.", 35, "ranged", "Small Guns", 80, 7.0, "10mm_patronen"),
    "bunker_jumpsuit": Armor("Vault-Tec Jumpsuit (Euro)", "Blue and yellow jumpsuit with the European Vault-Tec logo.", 5, "body", 50, 2.0),
    "lederharnisch": Armor("Lederharnisch (Leather Armor)", "Boiled leather strips reinforced with tires.", 15, "body", 120, 8.0),
    "raider_rags": Armor("Plünderer Lumpen", "Smells of oil and fear. Offers minimal protection.", 8, "body", 30, 5.0),
    "iron_ring_plate": Armor("Iron Ring Breastplate", "Heavy steel plate with the Red Eagle insignia.", 30, "body", 400, 25.0),
    "sani_pack": Consumable("Sani-Pack (Stimpak)", "Military grade healing injector. 'Nur für den Notfall'.", "heal", 30, 0, 75, 0.5),
    "jod_tabletten": Consumable("Jod-Tabletten (RadAway)", "Bitter tasting iodine tablets to flush radiation.", "rad_heal", 100, 0, 80, 0.2),
    "rad_blocker": Consumable("Rad-Blocker (Rad-X)", "Chemical cocktail that hardens cells against radiation.", "buff", 25, 300, 60, 0.2),
    "currywurst": Consumable("Irradiated Currywurst", "A Berlin classic. Glows slightly. Heals HP.", "heal", 15, 0, 10, 0.5),
    "berliner_weisse": Consumable("Berliner Weisse (Green)", "Syrupy beer. Increases charisma.", "buff", 1, 120, 15, 1.0),
    "doner_human": Consumable("Döner 'Spezial'", "Meat of questionable origin on flatbread.", "heal", 40, 0, 20, 1.0),
    "10mm_patronen": Ammo("10mm Patronen", "Standard pistol ammunition.", 10, 20, 0.1),
    "fusionszellen": Ammo("Fusionszellen", "Batteries for energy weapons.", 10, 30, 0.1),
    "anmeldung_form": Item("Formular A38 (Anmeldung)", "A bureaucratic nightmare required to enter the inner city.", 0, 0.0, "quest"),
    "caps": Item("Kronkorken (Caps)", "Bottle caps used as currency.", 1, 0.0, "currency")
}

ALIASES = {
    "stimpak": "sani_pack",
    "radaway": "jod_tabletten",
    "rad_x": "rad_blocker",
    "10mm_pistol": "pistole_10mm",
    "pipe_pistol": "rohrpistole",
    "knife": "kampfmesser",
    "leather_armor": "lederharnisch",
    "vault_suit": "bunker_jumpsuit",
    "10mm_rounds": "10mm_patronen",
    "fusion_cell": "fusionszellen",
    "doner_kebab": "doner_human"
}

def create_item(key: str, count: int = 1) -> Optional[Item]:
    key = key.lower()
    if key in ALIASES:
        key = ALIASES[key]
    
    # 1. Check hardcoded database
    if key in ITEM_DATABASE:
        template = ITEM_DATABASE[key]
        # Create a deep copy/new instance
        data = template.to_dict()
        data['item_id'] = key
        if isinstance(template, Ammo):
            data['quantity'] = count
        item = Item.from_dict(data)
        if item.item_type == "currency" and item.item_id == "caps":
            item.quantity = count
            item.stackable = True
        return item
    
    # 2. Check JSON database
    if key in ITEM_JSON_DATABASE:
        data = ITEM_JSON_DATABASE[key].copy()
        data['item_id'] = key
        # Handle quantity for ammo if specified in args
        if data.get('class') == 'Ammo' or data.get('item_type') == 'ammo':
             data['quantity'] = count
        item = Item.from_dict(data)
        if item.item_type == "currency" and item.item_id == "caps":
            item.quantity = count
            item.stackable = True
        return item

    return None