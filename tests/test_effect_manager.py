import contextlib
import io
import unittest

from fallout_berlin.effect_manager import EffectManager
from fallout_berlin.inventory import Inventory
from fallout_berlin.item import Consumable, Item, create_item
from fallout_berlin.player import Player


class EffectManagerTests(unittest.TestCase):
    def setUp(self):
        self.manager = EffectManager()
        self.player = Player("Test")
        self.inventory = Inventory()

    def apply_quietly(self, item):
        self.inventory.add_item(item)
        with contextlib.redirect_stdout(io.StringIO()):
            return self.manager.apply_effect(item, self.player, self.inventory)

    def test_medic_perk_applies_bonus_from_saved_perk_shape(self):
        self.player.perks = [{"name": "Medic"}]
        self.player.max_hit_points = 100
        self.player.hit_points = 1
        item = create_item("stimpak")

        self.assertTrue(self.apply_quietly(item))
        self.assertEqual(self.player.hit_points, 46)

    def test_food_and_drink_change_only_their_matching_survival_stat(self):
        self.player.hunger = 40
        self.player.thirst = 40

        self.assertTrue(self.apply_quietly(Consumable("Food", "", "food", 10)))
        self.assertEqual((self.player.hunger, self.player.thirst), (30, 40))
        self.assertTrue(self.apply_quietly(Consumable("Drink", "", "drink", 10)))
        self.assertEqual((self.player.hunger, self.player.thirst), (30, 30))

    def test_declared_major_heal_and_perception_buff_are_usable(self):
        self.player.hit_points = 1
        major_heal = create_item("schnitzel_supreme")
        self.assertTrue(self.apply_quietly(major_heal))
        self.assertGreater(self.player.hit_points, 1)

        before_perception = self.player.perception
        perception_buff = create_item("berliner_luft")
        self.assertTrue(self.apply_quietly(perception_buff))
        self.assertEqual(self.player.perception, before_perception + 2)

    def test_irradiated_food_heals_adds_radiation_and_round_trips(self):
        item = create_item("irradiated_currywurst")
        restored = Item.from_dict(item.to_dict())
        self.assertEqual(restored.radiation_damage, 10)

        self.player.hit_points = 1
        starting_radiation = self.player.radiation
        self.assertTrue(self.apply_quietly(item))
        self.assertGreater(self.player.hit_points, 1)
        self.assertEqual(self.player.radiation, starting_radiation + 10)
        self.assertFalse(self.inventory.has_item(item.name))

    def test_rad_heal_effect_reduces_radiation(self):
        self.player.radiation = 100
        radaway = Consumable("RadAway", "", "rad_heal", 30)

        self.assertTrue(self.apply_quietly(radaway))
        self.assertEqual(self.player.radiation, 70)


if __name__ == "__main__":
    unittest.main()