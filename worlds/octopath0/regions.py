from typing import TYPE_CHECKING

from BaseClasses import Entrance, Region

if TYPE_CHECKING:
    from .world import OctopathZeroWorld

def create_and_connect_regions(world: OctopathZeroWorld) -> None:
    create_all_regions(world)
    connect_regions(world)

# Currently does nothing.
def create_all_regions(world: OctopathZeroWorld) -> None:
    print()