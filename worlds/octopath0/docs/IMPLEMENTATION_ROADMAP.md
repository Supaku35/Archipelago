# Octopath Traveler 0 Archipelago implementation roadmap

**Current milestone · M2, a repeatable post-intro Wishvale start.** The two-room binding, chest submission and shield delivery playtest passed in-game, including crossed saves in both directions. Wishvale Candidate 01 passed the offline start playtest, including the Stia transition and disk reload. Candidate 02 also passed with a separately created Hunter. The native job picker now opens directly after customization in the opt-in Windows prototype. The next step is entering post-workshop Wishvale after job confirmation.

This is the working implementation order. The [original design notes](Octopath%200%20Archipelago.md) remain the reference for area inventories, route details, chapter thresholds and desired settings. The first proposed playable release targets **Master of All**, the design’s default goal. Bestower of All and Traveler Hunt have their own milestones. Milestone order is a recommendation. A playtest result can change it.

## Wishvale candidate 01

`tools/build_wishvale_start.py` creates a disposable offline slot from the verified pre-Stia reference. The builder recognizes the decoded reference by SHA-256. Supply that local save as the first argument and an unused output path as the second. For a compressed input, pass `--decoder` pointing to a trusted local Oodle library or libooz. An early, unbound `--character` save can supply appearance, primary job, job records, names and inventory. Early-play items and learned skills may carry over. Reference saves and generated slots stay private.

The packaged test character keeps the reference appearance and job. Both active travelers begin at LV1, 0 EXP, 0 current JP, 1 HP and 0 SP so the workshop bed can verify native recovery. The village, quest data, two unopened prototype chests and unbound room state match the natural reference on disk.

**2026-11-25 · Candidate 01 passed in game.** The player loaded Wren and Stia at LV1, recovered both at the workshop, and left and re-entered Wishvale. Accepting Rekindling the Flame Pt. 1 changed the objective from “Speak to Stia in Wishvale” to “Head to North Theatropolis Plains” while The Restoration Begins stayed at 0/1. Party level, objective and town counter persisted through a manual save and reload.

**2026-11-25 · Candidate 02 passed in game.** The separately created LV1 Hunter retained the chosen name, appearance, job, equipment, masteries, favorite dish and starting items in Wishvale. Workshop rest restored the Hunter to 250 HP and 45 SP. The party left and re-entered town, and a manual save and reload preserved the character and pre-Stia objective.

The slot preview showed the reference protagonist’s name and appearance at LV2 with Stia, even though loading the slot produced the correct LV1 Hunter. The cause is unverified. Revisit the preview if it recurs on a slot created through the normal New Game handoff. Final starting inventory tuning remains open.

**New Game sequence for an Archipelago run.** The normal game separates opening customization from primary-job selection with intro gameplay. Keep the opening choices, then send the player directly to the native primary-job picker. On confirmation, carry the selected protagonist and job-specific equipment and skills into LV1 Wishvale with Stia, the workshop built, and “Speak to Stia in Wishvale” available. The player should reach that state without playing the intervening intro or swapping a save file.

The [OT0 event opcode atlas](https://github.com/veganprimate/CotCPort/blob/main/Resources/Event/Event_Opcode_Crossref_Atlas.md) identifies opening event 501, row 32, command 5500 as the customization screen. Event 99120, row 9, uses command 5501 for native primary-job selection. In both natural saves, the event 99120 snapshot still has the intro job, and event 98034 already has the selected job.

**Menu sequence prototype, direct picker transition verified in game.** The optional UE4SS mod in `OctopathArchipelago/prototypes/OT0APStart` handles Ctrl+Alt+J during opening customization. It validates the current event and surrounding rows and schedules 5501 immediately after 5500. The test uses the game’s normal command interpreter. It changes only the next command in the current event instance. After the picker, the original intro branch resumes. The Windows player reported the requested picker retest passed. Cancel/back behavior was not separately reported. Standalone Lua tests cover matching, incompatible and ambiguous event contexts. The Windows header exposes the native save installation and level restart functions. Their call order and arguments during a normal load still need a runtime check.

The first Windows attempt reached the hotkey and found six event contexts without a readable active index. The prototype stopped before writing a command. The revised lookup reads the event IDs, locates the populated opening context, and verifies the creation, next-command and intro-branch rows before editing. Lua regression tests exercise the opening in each of six positions as well as missing and ambiguous targets. The player confirmed the revised build (`f40cc8d`) worked. The remaining live handoff is from job confirmation to the pre-Stia Wishvale checkpoint with the chosen character and job equipment.

**Native load observation.** The optional `OctopathArchipelago/prototypes/OT0APLoadTrace` mod uses Ctrl+Alt+L to bracket a normal load of the existing Wishvale slot. It records observed calls, including the save object, restart initialization flag and level argument when exposed, plus before/after snapshots of the active save and field level. `SaveDataUser.LastMapMsdID` and `LastTownMapMsdID` are distinct in the natural reference. Verify the destination from the active level as well as the save record. A function missing from the trace is inconclusive because direct native calls can bypass reflected hooks. The post-job handoff is pending.

**2026-11-25 · Candidate 02 loaded on Wishvale Trail.** All 18 trace hooks armed and four calls were observed, in order: `SaveLoadMenuBase:OnLoad`, `TitleUI:OnFinishLoadGame`, `LevelManager:LevelLoadedField`, and `LevelManager:LevelShownField`. The save object received by the title callback was the same object active after the field appeared. It carried Hunter job 6, last map 900011, last town 900002 and playing event 0. Both the active field name and load label were `Map_FP_Forest_N0_9001_A1` on the trail. `StartLevel` read `None` at both endpoints. No restart arguments or save-setter calls were observed. Calling the title callback from character creation has not been verified. The next comparison is a normal walk from the trail into Wishvale with the same trace, ending outdoors after control returns.

## What we can reproduce today

| Evidence | What it establishes |
|---|---|
| Original two-chest room, seed `74188682935974291198` | Wishvale submitted as `10170115` and a second run skipped it. Keep the shipped archive for compatibility tests. |
| Revised two-chest room, seed `84576831886948881492`, slot `OT0TwoChest` | The server recorded Wishvale as `10070115` and Cerulean as `10070117`. A reconnect skipped the previously submitted Wishvale check. The in-game watch uses treasure IDs `70115` and `70117`. The earlier timing change removed the observed once-per-second stutter. |
| Revised generator and server | Both seed profiles were exercised against a server. The revised archive has 168 catalog names, two active checks, and two Small Shield placements. Cerulean’s revised AP ID is `10070117`. The shield’s revised AP ID is `10110001`, game item `110001`. |
| Offline planner | 178 proposed chest mappings include the 168 catalog entries and ten draft entries. Another 198 records or placeholders are excluded. These counts describe this catalog snapshot. Each location still needs evidence for access rules, game observation and reward handling before activation. |
| Inbound delivery and native rewards | The original prototype has save binding, indexed item delivery and reconciliation. The mod has targeted suppression for the two prototype rewards. The revised sender verifies and submits checks. In the revised room, both shield deliveries persisted across reloads. Replaying index 0 preserved the count. Cerulean’s native Buckler was suppressed, and a fresh connection confirmed the two-shield goal. Campaign goals are covered in later milestones. |

Baseline code and fixtures are in [the catalog integration commit](https://github.com/Supaku35/Archipelago/commit/7685ee9be25530de46ec3afd3cda1b6f7af75d46). The relevant entry points are [world generation](../__init__.py), [the two-chest sender](../PythonSender/submit_two_chest.py), [reconciliation](../PythonSender/reconcile_ap_items.py) and [the archived seed tests](../test/test_seed_generation.py).

## Milestones and acceptance tests

| Order | Deliverable and dependency | Move on when |
|---|---|---|
| **M0 · Chest reporting** — passed for Wishvale | Preserve the original and revised fixtures and their pinned profiles. Keep the second chest available for the rest of the loop. | The server confirms the selected Wishvale ID and skips it on reconnect. The opposite profile refuses the room before the watch starts. |
| **M1 · Receive what the room sent** — passed in-game | Extend the existing reconciliation and delivery path to the revised profile. Start with read-only history, then one explicitly authorized grant. Use the same two checks to exercise receipt of two identical items at different delivery indices. | Opening each test chest yields one server check. Each received index grants one shield. The native reward is accounted for. Restart, disk reload and reconnect preserve the expected inventory and index. Report the test goal only after its condition holds. |
| **M2 · A seed, a save and a start** — room isolation and offline Wishvale start passed, character-creation handoff pending | After M1, let the client read supported mappings and enabled locations from versioned slot data. Bind the chosen game save to the room and slot. Build and verify a repeatable post-intro Wishvale start. This removes the need to hard-code each new seed. | Two independently generated seeds connect to their own saves. A mismatched room or save stops before any grant or check. A fresh save can leave and return to Wishvale, use the workshop, save and reload. All four intro pickups stay outside the pool. |
| **M3 · A small playable Frostlands route** | After M2, connect Wishvale, Wishvale Trail, Cerulean Caverns and West Emberglow Wilds by their actual exits. Enable a few verified easy chests. Add a small supported item pool with sufficient filler for every enabled location. | Walk the generated route on a fresh save. Open two checks out of order, pass through a map change, and reconnect. Enabled chests pay once, an ordinary chest outside the seed gives its vanilla reward, and idle play stays smooth. |
| **M4 · First progression item that opens a route** | Build on M3 with one region unlock and a real boundary, then both early branches into Flatlands and Woodlands. Model directed exits, story flags and Ribbon/party alternatives. Deliver a progression item from another slot. | Before the unlock, the game and generator agree that the destination is closed. After receipt, both agree which exits and checks open. An unlock for a disconnected region grants access once a connecting route exists. A two-player seed sends progression in both directions and survives reconnect. |
| **M5 · Early chapters, travelers and combat logic** | With routes working, implement Wealth, Power and Fame chapters 1–2 in small slices. Add recruit, key-item, influence and boss-clear events as their first chapters need them. Preserve Wishvale’s quest order. Extend the item pool with tested grants and equipment tiers. | Test a starting path through its second chapter. The Key to Auguste’s Villa and Documentation of Tytos’s Crimes each unlock the intended chapter step. Required recruits and keys are reachable before use. The generator and a playtester agree on the next beatable chapter. |
| **M6 · First campaign release candidate for Master of All** | Extend M4–M5 to the eight regions, the three Master chapter 3s and Master of All chapters 1–8. Collect missing boss/gear evidence in chapter order. Add the default goal’s actual game-completion event. | A fresh run reaches the final event under the supported settings without grinding for a required check. The final event reports goal once and reconnect preserves completion. A second slot receives a required item from an OT0 check. The OT0 player can finish with a required item received remotely. |
| **M7 · Alternative goals** | Traveler Hunt can branch from M5 once the required traveler roster, recruit triggers and availability are documented. Bestower of All follows M6 through the three Bestower arcs and Bestower of All chapters 1–8. | Hunt completes on the configured distinct traveler count, including boundary tests at 1 and 35. Verify the pre–Master of All placement option. Bestower reports only on its chosen ending. Completing an earlier story goal does not finish a Bestower seed. |
| **M8 · Optional checks, settings and release** | Add each optional family once its prerequisites below work. These can land independently of M7. Publish the supported combinations, installation steps, recovery procedure and a matched world/client/mod release. | Generate and finish representative solo and multiworld seeds. Exercise each enabled family in-game, verify disabled content retains its vanilla behavior, and have another player complete setup and reconnect using the release instructions. |

### M1 regression procedure

1. **Use the existing revised room.** Keep its server save with Wishvale checked and Cerulean missing. Extend the read-only reconciliation command to show the verified seed, slot, received index, source check, AP item, game item and saved next index. Opening this report must leave inventory and the delivery index untouched.
2. **Establish the save binding.** Use a test save with a known shield count. Inspect it first. Verify refusal on an original-room binding or a different slot. If the current game save is already bound to another seed, use a separate test save for the revised room. Record the room’s already-checked state.
3. **Authorize index 0 once.** Compare shield count before and after, save to disk, fully reload, then reconcile again. A replay of index 0 must preserve the count. If the grant outcome is uncertain, inspect the loaded save and server history before attempting another grant.
4. **Check Cerulean and process index 1.** Verify revised location `10070117`, the second shield and its own index. Check the native Buckler separately from the AP shield. Capture reward behavior on an unopened chest. An already-open observation can prove reporting only. Exercise the two-shield goal and reconnect.
5. **Record the evidence.** Keep the seed name, client/mod revision, server checked set, received indices, inventory deltas and post-reload result. M1 closes when these agree for both deliveries.

## Natural Wishvale reference

Captured in-game on 2026-11-24. These are observations from one naturally played save. The seeded start retains the LV1 protagonist target and applies starting inventory and chapter availability according to the chosen settings.

| Check | Observed state |
|---|---|
| Town | Wishvale, town level 1. Workshop is the only building. Its completion filled about one third of the town bar. |
| Restoration | **The Restoration Begins**, 0/1. The HUD directs the player to progress through the side story “Rekindling the Flame.” |
| Next story action | **Rekindling the Flame Pt. 1** is available. The menu says “Speak to Stia in Wishvale.” |
| Other available quests | Master of Power Ch. 1 — The Scarlet Tyrant. Master of Wealth Ch. 1 — The Covetous Witch. Master of Fame Ch. 1 — The Genius Playwright. |
| Workshop and travel | The workshop bed offers to restore HP and SP fully. Resting was the only workshop interaction reported. The player could leave Wishvale and re-enter freely. |
| Party | Protagonist and Stia each at LV6, 140 EXP, 48 EXP to the next level and 30 JP. Protagonist's primary job is a player choice among eight. |
| Map label | The game menu shows “Woodlands Region” over Wishvale. The design notes group the starting area under Frostlands. Resolve the AP region assignment when implementing region gates. |

**Reported inventory on this save**

| Category | Contents |
|---|---|
| Consumables | Healing Grape ×1, Olive of Life ×1, Energizing Pomegranate ×1, protagonist's favorite food ×1 |
| Equipment | Sword of the Watch ×1, Handaxe ×1, base equipment for the chosen job, Buckler ×1, Villager's Clothes ×1, Leather Vest ×1 |
| Character creation and masteries | Three chosen starting items ×1 each, Vacuum Slice Mastery ×1, two chosen skill masteries ×1 each |
| Materials and ring | Lumber ×4, Stone ×6, Cloth ×2, Ring of Aelfric the Flamebringer ×1 |

**2026-11-25 · First Stia conversation, verified in-game.** Before speaking to Stia, the menu says “Speak to Stia in Wishvale.” On the copy, accepting Rekindling the Flame Pt. 1 changed the objective to “Head to North Theatropolis Plains”. The town HUD still showed The Restoration Begins at 0/1. The player saved and reloaded the copy and observed the same quest objective and town counter.

**Seeded-start acceptance test.** Begin at the pre-conversation objective with the workshop available. Accept the quest from Stia, verify the North Theatropolis Plains objective and the 0/1 town counter, then save and reload and check both again. Compare the two natural save slots to identify candidate quest-state changes. The natural reference and offline Candidate 01 both passed this sequence. Repeat it once the new-game handoff is in place.


**2026-11-25 · Read-only save comparison.** The two natural saves each contain 105 quest records. Comparing complete serialized rows by `QuestMsdID` found exactly one changed row, `9001035`. The matching in-game objectives are recorded above.

| Field in quest 9001035 | Before speaking to Stia | After accepting and reloading |
|---|---:|---:|
| `SeqState` | 1 | 2 |
| `Progress` | 0 | 1 |
| `CurrentTaskID` | 0 | 90368 |
| `ClearNum` | 0 | 0 |
| `ClearTick` | 0 | 0 |

The row’s start and update timestamps also changed. Both saves already list `9001035` first in `SaveDataUser.QuestPriority`. The event list grew from 425 to 426 with one added row, `EventMsdID 99515`; all previously recorded events were byte-identical by ID. Treat that event as an observation until independently attributed. Party, inventory, treasure, village buildings, event flags and game variables were byte-identical in their respective top-level properties. Within `SaveDataVillage` only `CurrentBGM` changed. Playtime, position and battle count also differed between the saves.

Use the first three quest fields as a read-only comparison when testing a seeded start. Let the normal Stia interaction advance them. Both live saves contain the workshop. Their embedded event snapshots also preserve earlier village layouts.

**2026-11-25 · Workshop comparison from event snapshots.** The village and building arrays in events `99514` and `98036` show town level 1 with no entries in `HasBuildIds` and completed town tasks `[1001, 1002, 1003]`. Both live saves have level 1, `Initialized = 3` (snapshot value 1), `HasBuildIds = [1000, 2031, 2018, 2015]` and one additional completed task, `1004`. The later event `99515` contains a building array byte-identical to the live pre-Stia array.

Comparing the 344 building slots in event `98036` against live `BeforeStia` gives five changed slots. All five previously had `BuildingDataId = 0`; the other 339 rows match by parsed field values.

| DataIndex | BuildingDataId after | PosX | PosY |
|---:|---:|---:|---:|
| 130 | 1000 | 20 | 27 |
| 134 | 2031 | 18 | 23 |
| 145 | 2018 | 20 | 30 |
| 146 | 2015 | 21 | 30 |
| 163 | 2015 | 22 | 30 |

Use the layout and town-task list as read-only reference values for this save. The individual object names, the role of task `1004`, and the changes sufficient for a functioning workshop still need independent verification. Embedded snapshots cover village data, not a complete playable save. Validate the candidate start with the workshop rest prompt, round-trip travel and the recorded Stia transition.

## Rules the implementation must preserve

**Starting state and Wishvale.** Skip the intro and exclude its three chests and one hidden item. Target Wishvale with the workshop built, a LV1 protagonist, base gear for the chosen class and the Ring of Aelfric the Flamebringer. Preserve protagonist customization. Use the native customization and primary-job screens in sequence for an Archipelago start. Apply Frostlands access when regions are randomized, the Spurring Ribbon when selected, available Master arcs when chapters are vanilla, and any configured LV1 starting travelers. Keep Wishvale quest progression in sequence. Test instant crop growth and animal production in Path to Self-Sustainability against the next quest trigger.

**Geography and chapters.** A region item permits entry through a reachable exit. Build edges from the area and questline lists in the design notes. For example, test entry to Coastlands from Flatlands and via the long western route through Woodlands, Cliftlands, Riverlands, Sunlands and Highlands. Test the documented travel condition separately. An undiscovered exit marked with hashes in the notes needs an in-game traversal before it becomes a generator edge. Chapter access combines its region, predecessor, quest/key items and combat requirements. Treat a key’s pickup and the door or chapter flag it unlocks as separate events.

**Party strength and equipment.** Start balance tests at effective LV5 while preserving the actual LV1 start. The notes give hard-chest access on normal logic as at least eight party members and combined level ≥ area level × 10. Hard logic uses at least six and combined level ≥ area level × 8. Keep party size and combined level as independent requirements. For example, Master of Power chapter 2 has normal thresholds of six members and 90 combined levels, and hard thresholds of four and 60. Use the source’s chapter-specific values. Check the Sazantos/Elrica party-count exception under the applicable traveler modes. From the three Master chapter 3s onward, use shop-equivalent gear as the default minimum. Playtest with a weak party and ordinary travel XP. Decide how generator logic represents expected levels without assuming the player will grind.

**Catalog and save contract.** Track game ID, stable AP ID, area, prerequisites, check signal, native reward and enabled settings per location. Keep the PDF’s names as aliases where useful. For example, “West near Squirrel” and “West Stump Chest” refer to treasure 70115. Reserve existing AP IDs once shipped. Detect checks against the active slot’s locations. Scope native-reward replacement to those locations on the intended save. Model item grants separately from location detection. On reconnect, reconcile checks against the server and deliveries against ordered AP history plus the save’s next index. Distinguish an in-memory observation from a successful disk reload.

## Settings and content dependencies

These are design targets. Expose a setting to players when the generator, game behavior and test coverage support its choices.

| Family | Design target and first implementation dependency |
|---|---|
| Goal, starting path and chapters | Master of All by default, plus Bestower of All and Traveler Hunt. Starting path defaults to random among Wealth, Power and Fame. Regions default on, chapter randomization off. Build the vanilla sequence first. Randomized chapters need both physical gates and placement rules that keep their keys reachable. |
| Travelers | Optional Only by default, with All and None. Support 0–7 extra starting travelers (default 0) and explicit or random selection when enabled. Hunt forces All and zero extras. The target is 1–35, default 20. By default all traveler placements for Hunt must be at or before Master of All. Test availability before enabling that combination. |
| Miniboss and blue chests | Miniboss chests default to non-progression, with fully random and off modes. Blue chests default to locked/non-progression. Support locked or unlocked with either placement policy, plus off. Blue Lockpick defaults on, is forced on for locked/fully random and off for unlocked. Verify the physical lock, key delivery, reward replacement and pool restrictions. A hard blue chest needs both rule families. |
| Gear, skills and economy | Progressive Weapons off by default. Shopsanity off, equipment only or all, with shop costs 0.1–2.0× (default 1.0×). Skillsanity off, filler only or on. JP Tokens optional and off by default. Verify purchase/learn-once signals, money or JP costs and reload behavior before making a purchase or skill progression-bearing. Test the chapter-3 gear guarantee both enabled (default) and disabled with its difficulty warning. |
| Quest checks and collectibles | Questsanity off by default. Start with a documented quest such as The Last Cask, then test a quest with an influence requirement such as A Stubborn Master. Identify stable flags for keys, music scores and other pickups before activation. Confirm Wishvale advances in vanilla order under every quest setting. |
| Pacing and navigation | EXP and JP multipliers each 0.5–5.0×, default 1.0×. Spurring Ribbon defaults to start with, with randomized and vanilla-location choices. Chest Radar defaults on. Fast travel defaults to all visited locations, with visited towns only as the alternative. Verify the Ribbon and fast travel cannot bypass logical gates. Retest no-grind assumptions at low EXP. |

## Open questions and evidence to collect

| Resolve before | Question | Evidence that settles it |
|---|---|---|
| M2 | Which post-intro flags and customization choices produce a stable Wishvale start? | Compare a naturally reached workshop save with a fresh seeded start through the first quest, map transition and disk reload. |
| M3–M4 | Which additional chests can safely replace their native reward? Which map exits remain unknown? | Record before/open/after observations on unopened chests and traverse each candidate exit in both relevant story states. The ten draft mappings, blue chests with missing IDs and blank villa entries can be researched alongside other work. |
| M5 | How do party count, expected level, influence and gear become generator rules across starting paths? | Compare predicted reachable checks with weak-party runs. Record chapter, party members, combined levels, gear and ordinary XP. Resolve unknown key uses and Macy’s later Wishvale requirement individually. |
| M6–M7 | What are the missing chapter thresholds, durable winning flags and goal boundaries? | Capture pre/post-boss saves and a reload for each candidate ending. Confirm Traveler Hunt counts unique eligible travelers, including forced recruits under All. |
| M8 | Which optional checks, prices and resource gates remain practical in a multiworld? | Generate extreme-option seeds and follow a real progression route. Record any forced grind, purchase lockout or quest that can consume its own required item. |

## Keeping this guide current

At the end of each milestone, update the opening status and its table row in the same branch as the tested change. Add a dated evidence line with the build or commit, seed/slot, test performed and result. Identify whether the result came from generation, a server with simulated game input, or an in-game run with a disk reload. Carry an unresolved result into the next session as a named test. Revise the design notes when the intended player experience changes and this roadmap when the order or evidence changes.

**2026-11-20 · M0.** Catalog integration build `7685ee9`, revised seed `84576831886948881492`, slot `OT0TwoChest`. User confirmed the Wishvale in-game submission and reconnect procedure passed. Next evidence needed is the revised room’s inbound item history and its relationship to the selected game save.

**M1 · Revised reconciliation ready for in-game testing.** Run `PythonSender/reconcile_ap_items.py --profile revised` against the existing revised room. With only Wishvale checked, expect one history entry from location `10070115`. An unbound save reports an unknown next index. To bind the intended unbound test save, run `PythonSender/bind_ap_save.py --initialize --profile revised`, save normally, reload and rerun reconciliation. For an undelivered shield, expect saved next index 0 and one pending delivery. A mismatched save keeps its existing binding. Server tests covered zero, one and two checks using simulated game responses. In-game persistence, grant and goal tests are pending.

**2026-11-20 · M1, save binding passed in-game.** Revised room, Wishvale checked, Cerulean missing. The new save reloaded with the expected binding and one pending shield. The revised delivery command now processes one index per invocation. With the matching Lua mod loaded, run `PythonSender/deliver_ap_item.py --profile revised`, disarm after confirmation, save and reload, then reconcile. Expect next index 1, zero pending and one additional Small Shield. Reauthorize with `--profile revised --replay-index-zero` and verify the count and index hold. Inventory persistence and replay in-game are awaiting this test.

**2026-11-20 · M1, first delivery passed in-game.** On build `daa9ab7` the user confirmed the index 0 delivery, inventory and index after reload, and duplicate replay. For Cerulean, record Buckler and Small Shield counts separately before opening. The opening should submit `10070117` without adding either item. After the index 1 AP delivery, expect one additional Small Shield. Save, reload, and verify next index 2 with zero pending. Run `PythonSender/two_chest_goal.py --report-goal` after verifying those counts. A fresh invocation without arguments reads back the slot’s completion status. In-game results for this last sequence are pending.

**2026-11-20 · M1 complete in-game.** Build `506d03f`, seed `84576831886948881492`, slot `OT0TwoChest`. The user confirmed Cerulean submitted `10070117` with Buckler and Small Shield counts unchanged on opening. Delivery index 1 added one Small Shield. After saving and reloading, the shield persisted, the next index was 2 and zero deliveries were pending. The server confirmed the two-shield goal and a fresh connection read it back as complete.

**2026-11-24 · M2 generated-room tests.** The solo two-chest client reads schema 2 mappings from the connected slot, validates them against the AP data package and supported game operations, and checks the selected save before reporting a chest or delivering an item. Generator inputs 112001 and 112002 produced distinct rooms. The user completed the Windows playtest on build `67e2733`. Each matching save retained one Wishvale shield after reload. In both crossed pairings the watch rejected the chest check and delivery authorization failed before a grant.
