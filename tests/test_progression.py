import unittest
from types import SimpleNamespace

from fallout_berlin.enemy import Enemy, create_enemy
from fallout_berlin.player import Player
from fallout_berlin.quest import QuestManager


class ProgressionTests(unittest.TestCase):
    def test_player_perks_survive_save_load_and_old_saves_still_load(self):
        player = Player("Test")
        player.perks = [{"name": "Medic"}]

        restored = Player.from_dict(player.to_dict())
        legacy = Player.from_dict({"name": "Legacy"})

        self.assertTrue(restored.has_perk("Medic"))
        self.assertEqual(legacy.perks, [])

    def test_enemy_id_survives_save_load(self):
        enemy = create_enemy("radhund_alpha")

        restored = Enemy.from_dict(enemy.to_dict())

        self.assertEqual(restored.enemy_id, "radhund_alpha")

    def test_variant_kills_count_toward_generic_creature_objective(self):
        manager = QuestManager.__new__(QuestManager)
        game_state = SimpleNamespace(killed_creatures={"radhund_alpha": 4})
        condition = {
            "type": "killed_creature",
            "params": {"creature": "radhund", "min_count": 4},
        }

        self.assertTrue(manager.evaluate_condition(condition, game_state))


if __name__ == "__main__":
    unittest.main()