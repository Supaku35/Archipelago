LOCATION_NAME = "Cerulean Caverns - Southwest Cliff Chest"
LOCATION_ID = 10_000_001
TREASURE_ID = 70117

# Region, AP name, AP ID, game treasure ID. The first row is the default seed.
PROTOTYPE_CHEST = ("Cerulean Caverns", LOCATION_NAME, LOCATION_ID, TREASURE_ID)
TRAIL_CHEST = ("Wishvale Trail", "Wishvale Trail - West near Squirrel", 10_170_115, 70115)
TEST_CHESTS = (PROTOTYPE_CHEST, TRAIL_CHEST)

location_name_to_id = {name: ap_id for _, name, ap_id, _ in TEST_CHESTS}
