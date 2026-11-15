from typing import TYPE_CHECKING

from BaseClasses import Entrance, Region

if TYPE_CHECKING:
    from .world import OctopathZeroWorld

def create_and_connect_regions(world: OctopathZeroWorld) -> None:
    create_all_regions(world)
    connect_regions(world)

def create_all_regions(world: OctopathZeroWorld) -> None:
    # Create each region and their connections. Depending on settings, players may need to go to high level areas early.
    # A region here is dictated by danger level and location within the world. For the sake of simplicity, region level
    # ranges from 1-4 based on danger level required to get there, as well as the danger level of the area itself.

    # Frostlands 1 includes Wishvale, Wishvale Trail, Cerulean Caverns, Emberglow Wilds, West Emberglow Wilds,
    # Snowshard Grotto, Emberglow, ************. This region is ALWAYS available.
    frostlands1 = Region("Frostlands 1", world.player, world.multiworld)

    # Frostlands 2 includes Flamesgrace Wilds, Flamesgrace, Valley of the Flame, Path to the Cave of Origin,
    # Cave of Origin, ************. This requires a party with a combined stat total of #### between a max of 4 of the
    # highest stat total party members (including equipment).
    frostlands2 = Region("Frostlands 2", world.player, world.multiworld)

    # Flatlands 1 includes North Theatropolis Plains, Serpent's Burrow, Theatropolis Plains, Knights Ardante Garrison,
    # Theatropolis, ***********. This region is always available UNLESS randomize regions is enabled in the yaml.
    flatlands1 = Region("Flatlands 1", world.player, world.multiworld)

    # Flatlands 2 includes West Theatropolis Plains, Atlasdam Flats, and Atlasdam. This requires Flatlands 1 and a party
    # with a combined stat total of #### between a max of 4 of the highest stat total party members
    # (including equipment).
    flatlands2 = Region("Flatlands 2", world.player, world.multiworld)

    # Woodlands 1 includes Valore Trail, Auguste's Villa Exterior*, Valore, Path to Herminia's Manse, *********.
    # This region is always available UNLESS randomize regions is enabled in the yaml.
    woodlands1 = Region("Woodlands 1", world.player, world.multiworld)

    # Woodlands 2 includes West Valore Trail. This requires Woodlands 1 and a party with a combined state total of
    # #### between a max of 4 of the highest stat total party members.
    woodlands2 = Region("Woodlands 2", world.player, world.multiworld)

    # Woodlands 3 includes Victors Hollow Trail, Great Trees Tears, and Victors Hollow. This requires Woodlands 1,
    # Woodlands 2, and a party with a combined state total of #### between a max of 4 of the highest stat total
    # party members.
    woodlands3 = Region("Woodlands 3", world.player, world.multiworld)

    # Coastlands includes North Rippletide Coast, Rippletide Coast, and Rippletide. This requires Flatlands 1 and a
    # party with a combined stat total of #### between a max of 4 of the highest stat total party members
    # (including equipment).
    coastlands = Region("Coastlands", world.player, world.multiworld)

    # Clifflands includes Cragspear Pass, Gray Grotto, Cragspear, South Cragspear Pass, and Geist Canyon*? This requires
    # Woodlands 1, Woodlands 2, and a party with a combined stat total of #### between a max of 4 of the highest stat
    # total party members (including equipment).
    clifflands = Region("Clifflands", world.player, world.multiworld)

    # Highlands 1 includes North Sheperds Rock Pass, Cavern of Mists, Sheperds Rock Pass, Valley of Death, and
    # Sheperds Rock. This requires Flatlands 1, Coastlands, and a party with a combined stat total of #### between a
    # max of 4 of the highest stat total party members (including equipment).
    highlands1 = Region("Highlands 1", world.player, world.multiworld)

    # Highlands 2 includes Berecain Pass: Base, Berecain Pass, Sweltering Cave, and Berecain*. This requires
    # Flatlands 1, Coastlands, Highlands 1, and a party with a combined stat total of #### between a max of 4 of the
    # highest stat total party members (including equipment).
    highlands2 = Region("Highlands 2", world.player, world.multiworld)

    # Riverlands 1 includes Clearbrook Traverse, Clearbrook, Path to Waterpool Caves*, Waterpool Caves*,
    # and East Clearbrook Traverse. This requires Woodlands 1, Woodlands 2, Clifflands, and a party with a combined
    # stat total of #### between a max of 4 of the highest stat total party members (including equipment).
    riverlands1 = Region("Riverlands 1", world.player, world.multiworld)
    
    # Riverlands 2 includes Donescu Traverse and Misty Falls**. This requires Woodlands 1, Woodlands 2, Clifflands, and
    # a party with a combined stat total of #### between a max of 4 of the highest stat total party members
    # (including equipment).
    riverlands2 = Region("Riverlands 2", world.player, world.multiworld)

    # Sunlands 1 includes Eastern Sunshade Sands, Finesand Ruins*, Sunshade Sands, and Sunshade. This requires
    # (Flatlands 1, Coastlands, and Highlands 1 OR Woodlands 1, Woodlands 2, Clifflands, and Riverlands 1) AND a party
    # with a combined stat total of #### between a max of 4 of the highest stat total party members (including
    # equipment).
    sunlands1 = Region("Sunlands 1", world.player, world.multiworld)

    # Sunlands 2 includes Sufratalijah Sands and Sulfratalijah*. This requires (Flatlands 1, Coastlands, and Highlands 1
    # OR Woodlands 1, Woodlands 2, Clifflands, and Riverlands 1) AND Sunlands 1 AND a party with a combined stat total
    # of #### between a max of 4 of the highest stat total party members (including equipment).
    sunlands2 = Region("Sunlands 2", world.player, world.multiworld)

    # Innersea includes