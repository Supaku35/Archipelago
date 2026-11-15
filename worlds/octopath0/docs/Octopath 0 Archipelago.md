# **GENERAL NOTES**

* The intro should be skipped entirely.  
  * There are 3 chests, and 1 hidden item here. Remove them from the pool above all else.  
  * The game would ideally start in Wishvale, with the workshop already built.  
  * The player should be able to customize their protagonist (appearance, job, etc). It would be nice if we could have this in game, but it will likely be a yaml thing.  
* LV 5 is extremely easy to get to quickly, even solo. This should be the assumption for base power for testing’s sake, not LV 1\.  
* Hard chests require a party of at least 8 with a combined level of (AreaLV x 10\) on normal  mode runs. Hard mode requires a party of at least 6 with a combined level of (AreaLV x 8\)  
* Chapter party and level requirements vary greatly depending on the chapter boss. Outlined below are the requirements for logic, as tested:  
  * Master of Power Ch. 1: (LV 24 \| 4 Party Members) \| (LV 16 \| 3 Party Members)  
  * Master of Power Ch. 2: (LV 90 \| 6 Party Members) \| (LV 60 \| 4 Party Members)  
  * Master of Power Ch. 3: (LV ??? \| 8 Party Members)  
  * Master of Fame Ch. 1: (LV 24 \| 4 Party Members) \| (LV 16 \| 3 Party Members)  
  * Master of Fame Ch. 2: (LV 40 \| 4 Party Members) \| (LV 30 \| 3 Party Members)  
  * Master of Fame Ch. 3: (LV ??? \| 8 Party Members)  
  * Master of Wealth Ch. 1: (LV 24 \| 4 Party Members \| (LV 16 \| 3 Party Members)  
  * Master of Wealth Ch. 2: (LV 90 \| 6 Party Members) \| (LV 60 \| 4 Party Members)  
  * Master of Wealth Ch. 3: (LV ??? \| 8 Party Members)  
  * Master of All Ch. 1: (LV ??? \| 8 Party Members)  
  * Master of All Ch. 2: (LV ??? \| 8 Party Members)  
  * Master of All Ch. 3: (LV ??? \| 8 Party Members)  
  * Master of All Ch. 4: (LV ??? \| 8 Party Members)  
  * Master of All Ch. 5: (LV ??? \| 8 Party Members)  
  * Master of All Ch. 6: (LV ??? \| 8 Party Members)  
  * Master of All Ch. 7: (LV ??? \| 8 Party Members)  
  * Master of All Ch. 8: (LV ??? \| 8 Party Members)  
  * Bestower of Power Ch. 1: (LV ??? \| 8 Party Members)  
  * Bestower of Power Ch. 2: (LV ??? \| 8 Party Members)  
  * Bestower of Power Ch. 3: (LV ??? \| 8 Party Members)  
  * Bestower of Fame Ch. 1: (LV ??? \| 8 Party Members)  
  * Bestower of Fame Ch. 2: (LV ??? \| 8 Party Members)  
  * Bestower of Fame Ch. 3: (LV ??? \| 8 Party Members)  
  * Bestower of Wealth Ch. 1: (LV ??? \| 8 Party Members)  
  * Bestower of Wealth Ch. 2: (LV ??? \| 8 Party Members)  
  * Bestower of Wealth Ch. 3: (LV ??? \| 8 Party Members)  
  * Bestower of All Ch. 1: (LV ??? \| 8 Party Members)  
  * Bestower of All Ch. 2: (LV ??? \| 8 Party Members)  
  * Bestower of All Ch. 3: (LV ??? \| 8 Party Members)  
  * Bestower of All Ch. 4: (LV ??? \| 8 Party Members)  
  * Bestower of All Ch. 5: (LV ??? \| 8 Party Members)  
  * Bestower of All Ch. 6: (LV ??? \| 8 Party Members)  
  * Bestower of All Ch. 7: (LV ??? \| 8 Party Members)  
  * Bestower of All Ch. 8: (LV ??? \| 8 Party Members)  
* Crops should instantly grow in the ‘Path to Self-Sustainability’ line, and animals should instantly produce as well.  
* All party member/level requirements have been tested under the worst case scenario. My testing was done with the worst party members you could get, with 0 equipment whatsoever, no skills learnt, barely any items, and the lowest level reasonably possible without excessive grinding.  
* Checks that require a higher level should be placed at points in logic where the player would likely be at the proper level to get those checks WITHOUT GRINDING. Hard mode logic may be more lenient on this, but grinding is never the intended solution to any problem.  
* From Chapter 3 onwards, ensure the player has equipment that is greater than or equal to the expected equipment at this point. What equipment shops would typically sell at the player’s point in the game will be used to determine suitable equipment. Testing has been done according to this rule. This will be toggleable in the yaml with a warning that turning this off could result in very grindy or punishing seeds.  
* Any part of the Wishvale Questline should NOT be randomized. The progression simply wouldn’t work if it was.   
* Region unlocks allow players to explore any reachable areas within that region.

# **YAML OPTIONS**

* Goal  
  * Master of All (Default)  
  * Bestower of All  
  * Traveler Hunt  
* Starting Path  
  * Random (Default)  
  * Wealth  
  * Power  
  * Fame  
* EXP Multiplier (Default 1.0x)  
  * 0.5x \- 5.0x  
* JP Multiplier (Default 1.0x)  
  * 0.5x \- 5.0x  
* Randomize Miniboss Chests  
  * Non-Progression Only (Default)  
  * Fully Random  
  * Off  
* Randomize Blue Chests  
  * Locked, Non-Progression Only (Default)  
  * Locked, Fully Random  
  * Unlocked, Non-Progression Only  
  * Unlocked, Fully Random  
  * Off  
* Blue Lockpick (adds a custom item that unlocks blue chests to the pool)  
  * On (Default) (forced for Locked, Fully Random)  
  * Off (forced for Unlocked)  
* Randomize Regions  
  * On (Default)  
  * Off  
* Randomize Chapters  
  * Off (Default)  
  * On  
* Randomize Travelers  
  * Optional Only (Default)  
  * All (forced for Traveler Hunt)  
  * None  
* Extra Starting Travelers (Default 0\) (Only with Randomize Travelers) (Forced 0 for Traveler Hunt)  
  * 0 \- 7  
* Party Selection (Only with Extra Starting Travelers):  
  * Stia  
  * Alexia  
  * Viator  
  * Celsus  
  * Phenn  
  * Macy  
  * Delitia  
  * Saoirse  
  * Sazantos  
  * Tressa  
  * Pius  
  * Therion  
  * Ludo  
  * Primrose  
  * Laurana  
  * Olberic  
  * Alfyn  
  * H'aanit  
  * Esperre  
  * Elrica  
  * Heidne  
  * Goodwin  
  * Isla  
  * Carinda  
  * Xerc  
  * Cyrus  
  * Ophilia  
  * Reime  
  * Richard  
  * Bargello  
  * Alaune  
  * Tatloch  
  * Rondo	  
  * Solon  
  * Eltrix  
  * Random  
* Travelers Required for Traveler Hunt (Traveler Hunt Only) (Default 20\)  
  * 1 to 35  
* Don’t place Travelers in any locations after Master of All (Traveler Hunt Only)  
  * On (Default)  
  * Off  
* Progressive Weapons  
  * Off (Default)  
  * On  
* Shopsanity  
  * Off (Default)  
  * Equipment Only  
  * All  
* Shop Cost Multiplier (Default 1.0x)  
  * 0.1x \- 2.0x  
* Skillsanity  
  * Off (Default)  
  * Filler Only  
  * On  
* Learn Skills with JP Tokens (Recommended for Skillsanity)  
  * Off (Default)  
  * On  
* Questsanity  
  * Off (Default)  
  * On  
* Spurring Ribbon  
  * Start With (Default)  
  * Randomized  
  * Default Location (not recommended)  
* Guarantee Suitable Equipment for ‘Master of’ Chapter 3s Onwards  
  * Yes (Default)  
  * No \*Warning\! May result in grindy or punishing seeds.  
* Chest Radar  
  * Enabled (Default)  
  * Disabled  
* Fast Travel  
  * All Visited Locations (Default)  
  * Visited Towns Only

# **CHECKS BY AREA**

**Frostlands Region**

* Wishvale  
  * Stia (Automatic) \+1 Fame  
* Wishvale Trail (LV 1\)  
  * 2 Easy Chests  
* Cerulean Caverns (LV 2\)  
  * 1 Easy Chest  
* West Emberglow Wilds (LV 4\)  
  * 2 Easy Chests  
* Snowshard Grotto (LV 5\)  
  * 2 Easy Chests  
  * 1 Hard Chest  
  * 1 Blue Chest  
* Emberglow Wilds (LV 4\)  
  * 2 Easy Chests  
  * 1 Blue Chest  
* Snowbloom Ruins (LV 10\)  
  * 3 Easy Chests  
* Emberglow  
  * 1 Easy Chest  
  * 1 Blue Chest  
  * Macy (Req. Herb of Fortification) \+1 Wealth  
* Emberglow East District  
  * 1 Easy Chest  
  * 1 Music Score  
* Emberglow Laboratory Entrance (LV 6\)  
  * 2 Easy Chests  
  * 1 Hard Chest  
* Emberglow Slopes (LV 10\)  
  * 2 Easy Chests  
  * 1 Hard Chest  
* Flamesgrace Wilds (LV 30):  
  * 4 Easy Chests  
  * 1 Blue Chest  
* Flamesgrace  
  * 3 Easy Chests  
* Flamesgrace Cathedral: Entrance  
  * 1 Easy Chest  
  * 1 Music Score  
* Flamesgrace Cathedral  
  * 3 Easy Chests  
  * 1 Blue Chest

**Flatlands Region**

* North Theatropolis Plains (LV 4\)  
  * 2 Easy Chests  
* Serpent’s Burrow (LV 6\)  
  * 3 Easy Chests  
  * 1 Blue Chest  
* Theatropolis Plains (LV 4\)  
  * 2 Easy Chests  
  * 1 Blue Chest  
* Knights Ardante Garrison (LV 10\)  
  * 3 Easy Chests  
* Theatropolis  
  * 1 Easy Chest  
  * 1 Blue Chest  
  * Letter Fragment  
  * Alexia (Req. Entreat Alexia) \+1 Fame  
* Amphitheatre Entrance  
  * 1 Easy Chest  
* Amphitheatre  
  * None  
* West Theatropolis Plains (LV 39\)  
  * 4 Easy Chests  
* Atlasdam Flats (LV 39\)  
  * 3 Easy Chests  
  * 1 Blue Chest  
* Atlasdam  
  * 1 Easy Chest  
* Atlasdam Palace Gate  
  * 1 Music Score  
* Royal Academy of Atlasdam  
  * 1 Easy Chest  
* Atlasdam Palace  
  * 3 Easy Chests  
  * 1 Blue Chest

**Coastlands Region**

* North Rippletide Coast (LV 20\)  
  * 2 Easy Chests  
* Rippletide Coast (LV 20\)  
  * 2 Easy Chests  
  * 1 Blue Chest  
* Rippletide  
  * 3 Easy Chests  
  * 1 Blue Chest  
  * 1 Music Score  
  * Tressa (Req. LV 20 Party of 4\*) \+1 Wealth

**Highlands Region**

* North Shepherds Rock Pass (LV 29\)  
  * 2 Easy Chests  
* Cavern of Mists (LV 33\)  
  * 3 Easy Chests  
  * 1 Hard Chest  
  * 1 Blue Chest  
  * 1 Music Score  
* Shepherds Rock Pass (LV 29\)  
  * 2 Easy Chests  
  * 1 Blue Chest  
* Shepherds Rock  
  * 2 Easy Chests  
  * 1 Blue Chest  
* Shepherds Rock: Castle Square  
  * 3 Easy Chests  
  * 1 Music Score  
* Valley of Death: East (LV 30\)  
  * 4 Easy Chests  
* Valley of Death (LV 30\)  
  * 3 Easy Chests  
  * 1 Hard Chest  
* Valley of Death West (LV 30\)  
  * 4 Easy Chests  
* Berecain Pass: Base (LV 42\)  
  * 4 Easy Chests  
* Berecain Pass (LV 42\)  
  * 3 Easy Chests  
  * 1 Blue Chest  
* Sweltering Cave (LV 45\)  
  * 4 Easy Chests  
  * 1 Hard Blue Chest  
* Berecain  
  * 2 Easy Chests  
  * 1 Blue Chest

**Sunlands Region**

* Eastern Sunshade Sands (LV 28\)  
  * 2 Easy Chests  
* Finesand Ruins (LV 29\)  
  * 4 Easy Chests  
  * 1 Hard Chest  
  * 1 Blue Chest  
* Sunshade Sands (LV 28\)  
  * 2 Easy Chests  
  * 1 Blue Chest  
  * Heidne 1  
* Sunshade  
  * 2 Easy Chests  
  * 1 Blue Chest  
* Sulfratalijah Sands (LV 39\)  
  * 2 Easy Chests  
  * 1 Blue Chest  
* Sulfratalijah  
  * 1 Easy Chest  
  * 1 Blue Chest

**Riverlands Region**

* East Clearbrook Traverse (LV 27\)  
  * 3 Easy Chests  
* Clearbrook Traverse (LV 27\)  
  * 3 Easy Chests  
  * 1 Blue Chest  
* Clearbrook  
  * 2 Easy Chests  
  * 1 Blue Chest  
  * 1 Music Score  
* Donescu Traverse (LV 34\)  
  * 2 Easy Chests  
* Misty Falls (LV 38\)  
  * 3 Easy Chests  
  * 1 Hard Blue Chest

**Cliftlands Region**

* South Cragspear Pass (LV 24\)  
  * 3 Easy Chests  
* Cragspear Pass (LV 24\)  
  * 2 Easy Chests  
  * 1 Blue Chest  
* Gray Grotto (LV 25\)  
  * 4 Easy Chests  
* Gray Grotto: Depths (LV 25):  
  * 3 Easy Chests  
  * 1 Hard Chest  
* Cragspear  
  * 2 Easy Chests  
  * 1 Blue Chest  
  * 1 Music Score  
  * Pius (Req. None) \+1 Fame  
* Cragspear: Slums  
  * 4 Easy Chests  
* Castle Edoras Gate  
  * None

**Woodlands Region**

* Valore Trail (LV 4\)  
  * 1 Easy Chest  
  * 1 Blue Chest  
* Auguste’s Villa: Entrance (LV 10\)  
  * 3 Easy Chests  
*  Valore  
  * 2 Easy Chests  
  * Viator (Req. Crested Key) \+1 Wealth  
  * Crested Key (From Viator)  
* Valore: Main Boulevard  
  * 1 Blue Chest  
  * Celsus (Req. None) \+1 Fame  
* Path to Herminia’s Manse (LV 6\)  
  * 3 Easy Chests  
* Herminia’s Manse: Entrance (LV 6\)  
  * 3 Easy Chests  
  * 1 Hard Chest  
* West Valore Trail (LV 23\)  
  * 4 Easy Chests  
* Victors Hollow Trail (LV 34\)  
  * 3 Easy Chests  
  * 1 Blue Chest  
  * Bouquet of Hollowlilies (Macy Wishvale Item)  
* Great Tree’s Tears (LV 36\)  
  * 3 Easy Chests  
  * 1 Hard Chest (Stats \>= ????)  
* Victors Hollow  
  * 1 Easy Chest  
  * 1 Blue Chest  
* Victors Hollow: Arena Gate  
  * 1 Easy Chest  
  * 1 Music Score  
* Arena  
  * 2 Easy Chests  
*  Victors Hollow: Old Quarter  
  * 2 Easy Chests

# **CHECKS BY QUESTLINE**

**To Enrich the Town**

* None

**Rekindling the Flame Ch. 1**

* None

**Rekindling the Flame Ch. 2**

* Wishvale Level 3 \+1 Power, Fame, Wealth

**Rekindling the Flame Ch. 3**

* 

**Kindlers of the Flame Ch. 1**

* Phenn (LV 5 SOLO) \+1 Power  
* Wishvale Level 2 \+1 Power, Fame, Wealth

**Kindlers of the Flame Ch. 2**

* Farm/Ranch  
* 2 Radiant Cornerstones

**Master of Power Ch. 1**

* Emberglow Laboratory (LV 6\)  
  * 4 Easy Chests  
  * 1 Hard Chest  
  * 1 Music Score  
* \+1 Power

**Master of Power Ch. 2**

* \+1 Power

**Master of Fame Ch. 1**

* Amphitheatre Rehearsal Room (LV 6\)  
  * 4 Easy Chests  
* Amphitheatre Dressing Room (LV 6\)  
  * 2 Easy Chests  
  * 1 Hard Chest  
* \+1 Fame

**Master of Fame Ch. 2**

* Auguste’s Villa: Entrance (LV 10\)  
  * 1 Easy Chest  
  * Key to Auguste’s Villa  
* Auguste’s Villa  
  * 4 Easy Chests  
  * 1 Hard Chest  
  * 2 Music Scores  
* \+1 Fame

**Master of Wealth Ch. 1**

* Path to Herminia’s Manse\* (LV 6\)  
  * 1 Easy Chest  
* \+1 Wealth

**Master of Wealth Ch. 2**

* Subterranean Snow Ruins (LV 10\)  
  * 1 Easy Chest  
  * 1 Hard Chest  
* \+1 Wealth

# **CONNECTIONS BY AREA**

**Frostlands Region**

* Wishvale → Wishvale Trail  
* Wishvale Trail → Wishvale \| Cerulean Caverns \| West Emberglow Wilds \| North Theatropolis Plains  
* Cerulean Caverns → Wishvail Trail \| \#\#\#\#\#\#\#\#\#\#\#  
* West Emberglow Wilds → Wishvale Trail \| Snowshard Grotto \| Emberglow Wilds \| Flamesgrace Wilds \| Valore Trail  
* Snowshard Grotto → West Emberglow Wilds  
* Emberglow Wilds → West Emberglow Wilds \| Snowbloom Ruins \| Emberglow \| North Theatropolis Plains  
* Snowbloom Ruins → Emberglow Wilds \| \#\#\#\#\#\#\#\#\#\#\#\#  
* Emberglow → Emberglow Wilds \| Emberglow East District \| \#\#\#\#\#\#\#\#\#\#\#\#  
* Emberglow East District → Emberglow \| Emberglow Laboratory Entrance \| Emberglow Slopes  
* Emberglow Laboratory Entrance → Emberglow East District \| \#\#\#\#\#\#\#\#\#\#\#\#  
* Emberglow Slopes → Emberglow East District \| \#\#\#\#\#\#\#\#\#\#\#  
* Flamesgrace Wilds → West Emberglow Wilds \| Flamesgrace  
* Flamesgrace → Flamesgrace Wilds \| Flamesgrace Cathedral: Entrance \| \#\#\#\#\#\#\#\#\#\#\#\#  
* Flamesgrace Cathedral: Entrance → Flamesgrace \| Flamesgrace Cathedral  
* Flamesgrace Cathedral → Flamesgrace Cathedral: Entrance

**Flatlands Region**

* North Theatropolis Plains → Wishvale Trail \| Emberglow Wilds \| Serpent’s Burrow \| Theatropolis Plains  
* Serpent’s Burrow → North Theatropolis Plains  
* Theatropolis Plains → North Theatropolis Plains \| Knights Ardante Garrison \| Theatropolis \| North Rippletide Coast  
* Knights Ardante Garrison → Theatropolis Plains  
* Theatropolis → Theatropolis Plains \| Amphitheatre Entrance \| West Theatropolis Plains  
* Amphitheatre Entrance → Theatropolis \| Amphitheatre \| \#\#\#\#\#\#\#\#\#\#\#  
* Amphitheatre → Amphitheatre Entrance  
* West Theatropolis Plains → Theatropolis \| Atlasdam Flats  
* Atlasdam Flats → West Theatropolis Plains \| Atlasdam  
* Atlasdam → Atlasdam Flats \| Atlasdam Palace Gate  
* Atlasdam Palace Gate → Atlasdam \| Royal Academy of Atlasdam \| Atlasdam Palace  
* Royal Academy of Atlasdam → Atlasdam Palace Gate  
* Atlasdam Palace → Atlasdam Palace Gate

**Coastlands Region**

* North Rippletide Coast → Theatropolis Plains \| Rippletide Coast  
* Rippletide Coast → North Rippletide Coast \| Rippletide \| North Shepherds Rock Pass  
* Rippletide → Rippletide Coast

**Highlands Region**

* North Shepherds Rock Pass → Rippletide Coast \| Cavern of Mists \| Shepherds Rock Pass  
* Cavern of Mists → North Shepherds Rock Pass  
* Shepherds Rock Pass → North Shepherds Rock Pass \| Shepherds Rock \| Valley of Death: East \| Eastern Sunshade Sands  
* Shepherds Rock → Shepherds Rock Pass \| Shepherds Rock: Castle Square  
* Shepherds Rock: Castle Square → Shepherds Rock  
* Valley of Death: East → Shepherds Rock Pass \| Valley of Death  
* Valley of Death → Valley of Death: East \| Valley of Death West \| Berecain Pass: Base  
* Valley of Death West → Valley of Death \| \#\#\#\#\#\#\#\#\#\#  
* Berecain Pass: Base → Valley of Death \| Berecain Pass  
* Berecain Pass → Berecain Pass: Base \| Sweltering Cave \| Berecain  
* Sweltering Cave → Berecain Pass  
* Berecain \| Berecain Pass

**Sunlands Region**

* Eastern Sunshade Sands → Shepherds Rock Pass \| Finesand Ruins \| Sunshade Sands \| Sulfratalijah Sands  
* Finesand Ruins → Eastern Sunshade Sands  
* Sunshade Sands → Eastern Sunshade Sands \| Sunshade \| East Clearbrook Traverse  
* Sunshade → Sunshade Sands  
* Sulfratalijah Sands → Eastern Sunshade Sands \| Sulfratalijah \| \#\#\#\#\#\#\#\#\#\#\#\#  
* Sulfratalijah → Sulfratalijah Sands \| \#\#\#\#\#\#\#\#\#\#\#\#

**Riverlands Region**

* East Clearbrook Traverse → Sunshade Sands \| Clearbrook Traverse \| Donescu Traverse  
* Clearbrook Traverse → East Clearbrook Traverse \| Clearbrook \| South Cragspear Pass  
* Clearbrook → Clearbrook Traverse \| \#\#\#\#\#\#\#\#\#\#\#  
* Donescu Traverse → East Clearbrook Traverse \| Misty Falls \| \#\#\#\#\#\#\#\#\#\#\#

**Cliftlands Region**

* South Cragspear Pass → Clearbrook Traverse \| Cragspear Pass \| \#\#\#\#\#\#\#\#\#\#\#  
* Cragspear Pass → South Cragspear Pass \| Gray Grotto \| Cragspear \| West Valore Trail  
* Gray Grotto → Cragspear Pass \| Gray Grotto: Depths  
* Gray Grotto: Depths → Gray Grotto  
* Cragspear  → Cragspear Pass \| Cragspear Slums \| Castle Edoras Gate  
* Cragspear Slums → Cragspear \| \#\#\#\#\#\#\#\#\#\#\#  
* Castle Edoras Gate → Cragspear \| \#\#\#\#\#\#\#\#\#\#\# \| \#\#\#\#\#\#\#\#\#\#\#\#

**Woodlands Region**

* Valore Trail → West Emberglow Wilds \| Auguste’s Villa: Entrance \| Valore \| West Valore Trail  
* Auguste’s Villa: Entrance → Valore Trail \| \#\#\#\#\#\#\#\#\#\#\#\#  
* Valore → Valore Trail \| Valore: Main Boulevard  
* Valore: Main Boulevard → Valore \| Path to Herminia’s Manse \| Herminia’s Manse: Entrance\*  
* Path to Herminia’s Manse → Valore: Main Boulevard \| Herminia’s Manse: Entrance  
* West Valore Trail → Valore Trail \| Cragspear Pass \| Victors Hollow Trail  
* Victors Hollow Trail → West Valore Trail \| Great Tree’s Tears \| Victors Hollow  
* Great Tree’s Tears → Victors Hollow Trail  
* Victors Hollow → Victors Hollow Trail \| Victors Hollow: Arena Gate  
* Victors Hollow: Arena Gate → Victors Hollow \| Arena \| Victors Hollow: Old Quarter  
* Arena → Victors Hollow: Arena Gate \| \#\#\#\#\#\#\#\#\#\#\#\#  
* Victors Hollow: Old Quarter → Victors Hollow: Arena Gate

# **CONNECTIONS BY QUESTLINE**

**Rekindling the Flame Pt 1 (Req. Flatlands)**

* None

**Rekindling the Flame Pt. 2 (Req. Woodlands \+ 15 Recruits Minimum)**

* None

**Rekindling the Flame Pt. 3 (Req. Cliftlands \+ 20 Recruits Minimum)**

* 

**Kindlers of the Flame Ch. 1 (Req. None)**

* None

**Kindlers of the Flame Ch. 2 (Req. Coastlands)**

* None

**Master of Power Ch. 1 (Req. None)**

* Emberglow Laboratory

**Master of Power Ch. 2 (Req. Flatlands)**

* Delitia (After Chapter Finish) \+1 Power

**Master of Fame Ch. 1 (Req. Flatlands)**

* Amphitheatre Rehearsal Room  
* Amphitheatre Dressing Room

**Master of Fame Ch. 2 (Req. Woodlands)**

* Auguste’s Villa: Entrance (1 Chest)  
* Auguste’s Villa\*

**Master of Wealth Ch. 1 (Req. Woodlands)**

* Path to Herminia’s Manse (1 Chest)

**Master of Wealth Ch. 2 (Req. Woodlands)**

* Subterranean Snow Ruins

# **QUESTSANITY**

* Valore: The Last Cask (LV 7\)  
  * Requirements:  
    * Woodlands  
    * Flatlands  
  * Rewards:  
    * 1500 Leaves  
    * \+1 Wealth  
* Rippletide: A Stubborn Master (LV 21\)  
  * Requirements:  
    * Coastlands  
    * Flatlands  
    * Wealth \>= 8  
  * Rewards:  
    * Rainbow Shell Charm  
    * Quality Whiskey  
    * \+1 Power  
* Flamesgrace: Fetching Soulstones (LV 30\)  
  * Requirements:  
    * 3 Fire Soulstones  
  * Rewards:  
    * ???

# **STARTING STATE**

* LV1 Protagonist with base gear for yaml-chosen class  
* Ring of Aelfric the Flamebringer  
* \*Frostlands Region Access if regions are randomized  
* \*Spurring Ribbon if chosen in yaml  
* \*Master of Wealth, Fame, and Power if chapters are not randomized  
* \*0-7 additional LV1 base gear party members depending on yaml

# **FIRST ACCESSIBLE CHECKS**

**\*assumes regions and chapters are randomized**

* **Frostlands Region**  
  * Wishvale  
    * Stia (Automatic) \+1 Fame  
  * Wishvale Trail (LV 1\)  
    * 2 Easy Chests  
  * Cerulean Caverns (LV 2\)  
    * 1 Easy Chest  
  * West Emberglow Wilds (LV 4\)  
    * 2 Easy Chests  
  * Snowshard Grotto (LV 5\)  
    * 2 Easy Chests  
  * Emberglow Wilds (LV 4\)  
    * 2 Easy Chests  
  * Snowbloom Ruins (LV 10\)  
    * 3 Easy Chests  
  * Emberglow  
    * 1 Easy Chest  
  * Emberglow East District  
    * 1 Easy Chest  
    * 1 Music Score  
  * Emberglow Laboratory Entrance (LV 6\)  
    * 2 Easy Chests

    **\*If player has spurring ribbon or LV 10 party of 4**

  * Emberglow Slopes (LV 10\)  
    * 2 Easy Chests

    **\*If player has spurring ribbon or LV 26 party of 8**

  * Flamesgrace Wilds (LV 30):  
    * 4 Easy Chests  
  * Flamesgrace  
    * 3 Easy Chests  
  * Flamesgrace Cathedral: Entrance  
    * 1 Easy Chest  
    * 1 Music Score  
  * Flamesgrace Cathedral  
    * 3 Easy Chests

# **PROGRESSION ITEMS**

* Woodlands Region Unlock  
  * Valore Trail (LV 4\)  
    * 1 Easy Chest  
  *  Valore  
    * 2 Easy Chests  
  * Valore: Main Boulevard  
    * Celsus (Req. None) \+1 Fame  
  * Path to Herminia’s Manse (LV 6\)  
    * 3 Easy Chests  
  * Herminia’s Manse: Entrance (LV 6\)  
    * 3 Easy Chests

    **\*If player has spurring ribbon or LV 10 party of 4**

  * Auguste’s Villa: Entrance (LV 10\)  
    * 3 Easy Chests

    **\*If player has spurring ribbon or LV 20 party of 8**

  * West Valore Trail (LV 23\)  
    * 4 Easy Chests

    **\*If player has spurring ribbon or LV 32 party of 8**

  * Victors Hollow Trail (LV 34\)  
    * 3 Easy Chests  
    * Bouquet of Hollowlilies (Macy Wishvale Item)  
  * Great Tree’s Tears (LV 36\)  
    * 3 Easy Chests  
  * Victors Hollow  
    * 1 Easy Chest  
  * Victors Hollow: Arena Gate  
    * 1 Easy Chest  
    * 1 Music Score  
  * Arena  
    * 2 Easy Chests  
  *  Victors Hollow: Old Quarter  
    * 2 Easy Chests

* Flatlands Region Unlock  
  * North Theatropolis Plains (LV 4\)  
    * 2 Easy Chests  
  * Serpent’s Burrow (LV 6\)  
    * 3 Easy Chests  
  * Theatropolis Plains (LV 4\)  
    * 2 Easy Chests  
  * Theatropolis  
    * 1 Easy Chest  
    * Letter Fragment  
    * Alexia (Req. Entreat Alexia) \+1 Fame  
  * Amphitheatre Entrance  
    * 1 Easy Chest  
  * Amphitheatre  
    * None

    **\*If player has spurring ribbon or LV 10 party of 4**

  * Knights Ardante Garrison (LV 10\)  
    * 3 Easy Chests

    **\*If player has spurring ribbon or LV 35 party of 8**

  * West Theatropolis Plains (LV 39\)  
    * 4 Easy Chests  
  * Atlasdam Flats (LV 39\)  
    * 3 Easy Chests  
  * Atlasdam  
    * 1 Easy Chest  
  * Atlasdam Palace Gate  
    * 1 Music Score  
  * Royal Academy of Atlasdam  
    * 1 Easy Chest  
  * Atlasdam Palace  
    * 3 Easy Chests

* Coastlands Region Unlock  
  **\*ACCESSIBLE ONLY WITH ((Flatlands) \| (Woodlands \+ Cliftlands \+ Riverlands \+ Sunlands \+ Highlands)) \+ (Spurring Ribbon \| LV 20 Party of 8\)**  
  * North Rippletide Coast (LV 20\)  
    * 2 Easy Chests  
  * Rippletide Coast (LV 20\)  
    * 2 Easy Chests  
  * Rippletide  
    * 3 Easy Chests  
    * 1 Music Score


* Cliftlands Region Unlock  
  **\*ACCESSIBLE ONLY WITH ((Woodlands) \| (Flatlands \+ Coastlands \+ Highlands \+ Sunlands \+ Riverlands)) \+ (Spurring Ribbon \| LV 24 Party of 8\)**  
  * South Cragspear Pass (LV 24\)  
    * 3 Easy Chests  
  * Cragspear Pass (LV 24\)  
    * 2 Easy Chests  
  * Gray Grotto (LV 25\)  
    * 4 Easy Chests  
  * Gray Grotto: Depths (LV 25):  
    * 3 Easy Chests  
  * Cragspear  
    * 2 Easy Chests  
    * 1 Music Score  
    * Pius (Req. None) \+1 Fame  
  * Cragspear: Slums  
    * 4 Easy Chests  
  * Castle Edoras Gate  
    * None

* Highlands Region Unlock  
  **\*ACCESSIBLE ONLY WITH ((Flatlands \+ Coastlands) \| (Woodlands \+ Cliftlands \+ Riverlands \+ Sunlands)) \+ (Spurring Ribbon \| LV 30 Party of 8\)**  
  * North Shepherds Rock Pass (LV 29\)  
    * 2 Easy Chests  
  * Cavern of Mists (LV 33\)  
    * 3 Easy Chests  
    * 1 Music Score  
  * Shepherds Rock Pass (LV 29\)  
    * 2 Easy Chests  
  * Shepherds Rock  
    * 2 Easy Chests  
  * Shepherds Rock: Castle Square  
    * 3 Easy Chests  
    * 1 Music Score  
  * Valley of Death: East (LV 30\)  
    * 4 Easy Chests  
  * Valley of Death (LV 30\)  
    * 3 Easy Chests  
  * Valley of Death West (LV 30\)  
    * 4 Easy Chests

    **\*If player has spurring ribbon or LV 40 party of 8**

  * Berecain Pass: Base (LV 42\)  
    * 4 Easy Chests  
  * Berecain Pass (LV 42\)  
    * 3 Easy Chests  
  * Sweltering Cave (LV 45\)  
    * 4 Easy Chests  
  * Berecain  
    * 2 Easy Chests

* Riverlands Region Unlock  
  **\*ACCESSIBLE ONLY WITH ((Woodlands \+ Cliftlands) \| (Flatlands \+ Coastlands \+ Highlands \+ Sunlands)) \+ (Spurring Ribbon \| LV 25 Party of 8\)**  
  * East Clearbrook Traverse (LV 27\)  
    * 3 Easy Chests  
  * Clearbrook Traverse (LV 27\)  
    * 3 Easy Chests  
  * Clearbrook  
    * 2 Easy Chests  
    * 1 Music Score

    **\*If player has spurring ribbon or LV 35 party of 8**

  * Donescu Traverse (LV 34\)  
    * 2 Easy Chests  
  * Misty Falls (LV 38\)  
    * 3 Easy Chests

* Sunlands Region Unlock  
  **\*ACCESSIBLE ONLY WITH ((Flatlands \+ Coastlands \+ Highlands) \| (Woodlands \+ Cliftlands \+ Riverlands)) \+ (Spurring Ribbon \| LV 26 Party of 8\)**  
  * Eastern Sunshade Sands (LV 28\)  
    * 2 Easy Chests  
  * Finesand Ruins (LV 29\)  
    * 4 Easy Chests  
  * Sunshade Sands (LV 28\)  
    * 2 Easy Chests  
  * Sunshade  
    * 2 Easy Chests

    **\*If player has spurring ribbon or LV 35 party of 8**

  * Sulfratalijah Sands (LV 39\)  
    * 2 Easy Chests  
  * Sulfratalijah  
    * 1 Easy Chest

* Total Party Members (Any except Sazantos or Elrica when party members randomized is off or optional party members randomized only is on) (a chapter is beatable under conditions outlined in the general notes section of the document)  
  * 3 Party Members  
    * Master of Wealth, Power, and Fame Ch. 1s beatable on hard mode.  
    * Master of Fame Ch. 2 beatable on hard mode.  
  * 4 Party Members  
    * Master of Wealth, Power, and Fame Ch. 1s beatable on normal mode.  
    * Master of Fame Ch. 2 beatable on normal mode.  
    * Master of Wealth and Power Ch. 2s beatable on hard mode.  
  * 6 Party Members  
    * Master of Wealth and Power Ch 2s beatable on normal mode.  
  * 8 Party Members  
    * All chapters beatable on normal and hard mode.

* Chapter Unlock (assuming chapter is beatable and region-accessible, see above, connections by area, connections by questline, and general notes section)  
  * Master of Wealth Ch. 1  
    * Path to Herminia’s Manse\* (LV 6\)  
      * 1 Easy Chest  
    * \+1 Wealth (on boss defeat)  
  * Master of Wealth Ch. 2  
    * Subterranean Snow Ruins (LV 10\)  
      * 1 Easy Chest  
    * \+1 Wealth (on boss defeat)  
  * Master of Wealth Ch. 3  
  * Master of Power Ch. 1  
    * Emberglow Laboratory (LV 6\)  
      * 4 Easy Chests  
      * 1 Hard Chest  
      * 1 Music Score  
    * \+1 Power (on boss defeat)  
  * Master of Power Ch. 2  
    * Documentation of Tytos's Crimes check  
  * Master of Power Ch. 3  
  * Master of Fame Ch. 1  
    * Amphitheatre Rehearsal Room (LV 6\)  
      * 4 Easy Chests  
    * Amphitheatre Dressing Room (LV 6\)  
      * 2 Easy Chests  
      * 1 Hard Chest  
    * \+1 Fame (on boss defeat)  
  * Master of Fame Ch. 2

    \*One of the only chapters that cannot be beaten without key item

    * Auguste’s Villa: Entrance (LV 10\)  
      * 1 Easy Chest  
      * Key to Auguste’s Villa (check)  
  * Master of Fame Ch. 3  
  * Master of All Ch. 1  
  * Master of All Ch. 2  
  * Master of All Ch. 3  
  * Master of All Ch. 4  
  * Master of All Ch. 5  
  * Master of All Ch. 6  
  * Master of All Ch. 7  
  * Master of All Ch. 8  
  * Bestower of Wealth Ch. 1  
  * Bestower of Wealth Ch. 2  
  * Bestower of Wealth Ch. 3  
  * Bestower of Power Ch. 1  
  * Bestower of Power Ch. 2  
  * Bestower of Power Ch. 3  
  * Bestower of Fame Ch. 1  
  * Bestower of Fame Ch. 2  
  * Bestower of Fame Ch. 3  
  * Bestower of All Ch. 1  
  * Bestower of All Ch. 2  
  * Bestower of All Ch. 3  
  * Bestower of All Ch. 4  
  * Bestower of All Ch. 5  
  * Bestower of All Ch. 6  
  * Bestower of All Ch. 7  
  * Bestower of All Ch. 8

* Key Item Unlock  
  * Key to Auguste’s Villa

    **\*Requires Master of Fame Ch. 2 and allows for chapter completion.**

    * Auguste’s Villa  
      * 4 Easy Chests  
      * 1 Hard Chest  
      * 2 Music Scores  
    * \+1 Fame (on boss defeat)  
  * Documentation of Tytos's Crimes

    **\*Requires Master of Power Ch. 2 and allows for chapter completion.**

    * \+1 Power (on boss defeat)  
  * Herb of Fortification (The first one acquired is treated as a key item)  
    * Macy \+1 Wealth  
  * Bouquet of Hollowlilies  
    * Macy Wishvale LV X \+ 1 Wealth  
  * Letter Fragment  
    *   
  * Crested Key  
    * 

* Blue Lockpick (Custom Item)  
  * Place all **accessible** blue chests in logic (assuming they’re randomized and locked)

* Hard Chests  
  * Placed in logic according to the rule in general notes (assuming they’re randomized to begin with). 