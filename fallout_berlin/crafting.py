import json
import os
from typing import Dict, List, Optional
from fallout_berlin.item import create_item

class CraftingManager:
    """Manages crafting recipes and item creation"""
    
    def __init__(self):
        self.recipes: Dict[str, Dict] = {}
        self._load_recipes()
    
    def _load_recipes(self):
        """Load recipes from JSON file"""
        data_path = os.path.join(os.path.dirname(__file__), 'data', 'recipes.json')
        if not os.path.exists(data_path):
            return
            
        try:
            with open(data_path, 'r', encoding='utf-8') as f:
                self.recipes = json.load(f)
        except Exception as e:
            print(f"Error loading recipes: {e}")
            
    def get_available_recipes(self, inventory, player_stats) -> List[str]:
        """Get recipes that the player can currently craft based on materials"""
        available = []
        for recipe_id, recipe in self.recipes.items():
            if self.can_craft(recipe_id, inventory, player_stats):
                available.append(recipe_id)
        return available
        
    def can_craft(self, recipe_id: str, inventory, player_stats) -> bool:
        """Check if a recipe can be crafted"""
        if recipe_id not in self.recipes:
            return False
            
        recipe = self.recipes[recipe_id]
        
        # Check skill requirement
        if 'skill_requirement' in recipe:
            skill = recipe['skill_requirement']['skill']
            min_val = recipe['skill_requirement']['min_value']
            if player_stats.get_skill(skill) < min_val:
                return False
                
        # Check materials
        for item_name, quantity in recipe['requirements'].items():
            if not inventory.has_item(item_name, quantity):
                return False
                
        return True
        
    def craft(self, recipe_id: str, inventory, player_stats) -> Optional[str]:
        """Attempt to craft an item"""
        if not self.can_craft(recipe_id, inventory, player_stats):
            return None
            
        recipe = self.recipes[recipe_id]
        
        # Remove materials
        for item_name, quantity in recipe['requirements'].items():
            inventory.remove_item(item_name, quantity)
            
        # Add result
        result_item = create_item(recipe['result'], recipe['result_quantity'])
        if result_item:
            inventory.add_item(result_item)
            return result_item.name
            
        return None
