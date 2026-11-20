"""Identities and mappings pinned to the two shipped OT0TwoChest archives."""
from ap_connection import verified_connection


# This describes the shipped archive, independently of current world definitions.
SEED = "74188682935974291198"
PLAYER = "OT0TwoChest"
SLOT_DATA = {
    "prototype_schema": 2,
    "prototype_goal": "receive_two_small_shields",
    "locations": [
        {"name": "Cerulean Caverns - Southwest Cliff Chest",
         "ap_location_id": 10000001, "game_treasure_id": 70117},
        {"name": "Wishvale Trail - West near Squirrel",
         "ap_location_id": 10170115, "game_treasure_id": 70115},
    ],
    "items": [{"name": "Small Shield", "ap_item_id": 10000002,
               "game_item_id": 110001, "quantity": 1}],
}


REVISED_SEED = "84576831886948881492"
REVISED_SLOT_DATA = {
    "prototype_schema": 2,
    "prototype_goal": "receive_two_small_shields",
    "locations": [
        {"name": "Cerulean Caverns - Southwest Cliff Chest",
         "ap_location_id": 10070117, "game_treasure_id": 70117},
        {"name": "Wishvale Trail - West Stump Chest",
         "ap_location_id": 10070115, "game_treasure_id": 70115},
    ],
    "items": [{"name": "Small Shield", "ap_item_id": 10110001,
               "game_item_id": 110001, "quantity": 1}],
}
# SHA-256 of the revised archive's full name-to-ID map in sorted compact JSON.
REVISED_CATALOG_DIGEST = "af5485eb136acb4c62f4c7878b0d52031c8486aa1270485139f2eb7d9fa5578b"
PROFILES = {
    "original": (SEED, SLOT_DATA, None),
    "revised": (REVISED_SEED, REVISED_SLOT_DATA, REVISED_CATALOG_DIGEST),
}


async def verify_revised_room(after_verified=None):
    return await verified_connection(REVISED_SEED, PLAYER, REVISED_SLOT_DATA, after_verified,
                                     catalog_digest=REVISED_CATALOG_DIGEST)
