from BaseClasses import Item, ItemClassification, Location, Region
from Options import PerGameCommonOptions
from worlds.AutoWorld import World

from .items import ITEM_NAME, ITEM_ID, GAME_ITEM_ID, item_name_to_id
from .locations import (
    LOCATION_NAME,
    LOCATION_ID,
    TREASURE_ID,
    location_name_to_id,
)


GAME_NAME = "Octopath Traveler 0"


class Octopath0Item(Item):
    game = GAME_NAME


class Octopath0Location(Location):
    game = GAME_NAME


class Octopath0World(World):
    """One-chest integration prototype; full game logic is not implemented."""

    game = GAME_NAME

    options_dataclass = PerGameCommonOptions
    options: PerGameCommonOptions

    topology_present = True

    item_name_to_id = item_name_to_id
    location_name_to_id = location_name_to_id

    def create_regions(self):
        menu = Region("Menu", self.player, self.multiworld)
        cavern = Region("Cerulean Caverns", self.player, self.multiworld)

        cavern.locations.append(
            Octopath0Location(
                self.player,
                LOCATION_NAME,
                LOCATION_ID,
                cavern,
            )
        )

        self.multiworld.regions.extend([menu, cavern])
        menu.connect(cavern)

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
        self.multiworld.itempool.append(self.create_item(ITEM_NAME))

    def set_rules(self):
        # Generator goal only; this does not report a goal to a live server.
        self.multiworld.completion_condition[self.player] = (
            lambda state: state.has(ITEM_NAME, self.player)
        )

    def get_filler_item_name(self):
        return ITEM_NAME

    def fill_slot_data(self):
        return {
            "prototype_schema": 1,
            "prototype_goal": "receive_small_shield",
            "locations": [{
                "name": LOCATION_NAME,
                "ap_location_id": LOCATION_ID,
                "game_treasure_id": TREASURE_ID,
            }],
            "items": [{
                "name": ITEM_NAME,
                "ap_item_id": ITEM_ID,
                "game_item_id": GAME_ITEM_ID,
                "quantity": 1,
            }],
        }