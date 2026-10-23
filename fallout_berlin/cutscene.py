"""
Cutscene Manager for Fallout Berlin
Handles narrative sequences and scripted events.
"""
from typing import Dict, Any

class CutsceneManager:
    def __init__(self, ui_manager):
        self.ui_manager = ui_manager
        self.scenes = {}

    def play_cutscene(self, scene_id: str):
        """Play a cutscene by ID"""
        if scene_id in self.scenes:
            # Placeholder for actual cutscene logic
            print(f"Playing cutscene: {scene_id}")
        else:
            print(f"Cutscene '{scene_id}' not found.")

    def register_scene(self, scene_id: str, scene_data: Dict[str, Any]):
        self.scenes[scene_id] = scene_data
