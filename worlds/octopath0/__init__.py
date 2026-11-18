from dataclasses import dataclass

from BaseClasses import Item, ItemClassification, Location, Region
from Options import PerGameCommonOptions, Toggle
from worlds.AutoWorld import World

from .items import ITEM_NAME, ITEM_ID, GAME_ITEM_ID, item_name_to_id
from .locations import PROTOTYPE_CHEST, TEST_CHESTS, location_name_to_id


GAME_NAME = "Octopath Traveler 0"


class TwoChestTest(Toggle):
    """Include the Wishvale Trail chest and require both Small Shields for the test goal."""
    display_name = "Two-Chest Integration Test"


@dataclass
class Octopath0Options(PerGameCommonOptions):
    two_chest_test: TwoChestTest


class Octopath0Item(Item):
    game = GAME_NAME


class Octopath0Location(Location):
    game = GAME_NAME


class Octopath0World(World):
    """Chest integration prototype with an optional two-chest test."""

    game = GAME_NAME

    options_dataclass = Octopath0Options
    options: Octopath0Options

    topology_present = True

    item_name_to_id = item_name_to_id
    location_name_to_id = location_name_to_id

    @property
    def test_chests(self):
        return TEST_CHESTS if self.options.two_chest_test else (PROTOTYPE_CHEST,)

    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        self.multiworld.regions.append(menu)
        for area, name, ap_id, _ in self.test_chests:
            region = Region(area, self.player, self.multiworld)
            self.multiworld.regions.append(region)
            region.locations.append(Octopath0Location(self.player, name, ap_id, region))
            menu.connect(region)

    def create_item(self, name):
        if name not in item_name_to_id:
            raise KeyError(f"Unknown Octopath 0 prototype item: {name}")

        # Progression only because this item is the temporary test goal.
        return Octopath0Item(
            name,
            ItemClassification.progression,
            item_name_to_id[name],
            self.player,
        )

    def create_items(self):
        for _ in self.test_chests:
            self.multiworld.itempool.append(self.create_item(ITEM_NAME))

    def set_rules(self):
        # Generator goal only; this does not report a goal to a live server.
        self.multiworld.completion_condition[self.player] = (
            lambda state: state.has(ITEM_NAME, self.player, len(self.test_chests))
        )

    def get_filler_item_name(self):
        return ITEM_NAME

    def fill_slot_data(self):
        return {
            "prototype_schema": 2 if self.options.two_chest_test else 1,
            "prototype_goal": "receive_two_small_shields" if self.options.two_chest_test else "receive_small_shield",
            "locations": [
                {"name": name, "ap_location_id": ap_id, "game_treasure_id": treasure_id}
                for _, name, ap_id, treasure_id in self.test_chests
            ],
            "items": [{
                "name": ITEM_NAME,
                "ap_item_id": ITEM_ID,
                "game_item_id": GAME_ITEM_ID,
                "quantity": 1,
            }],
        }
