from BaseClasses import Region


def create_test_regions(world, location_type):
    menu = Region("Menu", world.player, world.multiworld)
    world.multiworld.regions.append(menu)
    for area, name, ap_id, _ in world.test_chests:
        region = Region(area, world.player, world.multiworld)
        world.multiworld.regions.append(region)
        region.locations.append(location_type(world.player, name, ap_id, region))
        menu.connect(region)
