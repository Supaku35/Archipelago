# Two generated rooms, two bound saves

This Windows playtest exercises the solo two-chest preset with two independently generated seeds. Both use player `OT0TwoChest`, team 0 and slot 1. Keep the completed M1 room and save for regressions.

## Prepare the client and two game slots

Close the game and stop the old AP server. In PowerShell:

```powershell
Set-Location D:\Archipelago
git switch integration/chest-catalog
git pull --ff-only
git submodule update --init -- OctopathArchipelago
$mod = 'D:\SteamLibrary\steamapps\common\Octopath_Traveler0\Octopath_Traveler0\Binaries\Win64\ue4ss\Mods\OctopathArchipelago\scripts'
Copy-Item .\OctopathArchipelago\scripts\main.lua,.\OctopathArchipelago\scripts\OT0AP_BridgeProtocol.lua -Destination $mod -ErrorAction Stop

$py = '.\.venv-ot0\Scripts\python.exe'
$world = '.\worlds\octopath0'
$rooms = '.\output\ot0-generated-room-test'
foreach ($number in 112001,112002) {
    & $py .\Generate.py --seed $number --player_files_path "$world\Players_OT0TwoChest" --outputpath $rooms --spoiler 0
    if ($LASTEXITCODE -ne 0) { throw "Generation failed for $number" }
}
```

| Room | Generator input | Server seed name with this build |
|---|---|---|
| A | 112001 | `09923417857535490215` |
| B | 112002 | `29768774052967974303` |

Use the seed name printed in each generated ZIP filename, including leading zeroes. Open the game and prepare **two separate unbound game slots**, A and B. You can save the same fresh, unbound playthrough to two slots **before initializing either**. Keep track of which slot is which. An existing M1 binding follows a save when copied.

## Bind each save once

Use the first window for the server. Set the seed to A, then start its ZIP:

```powershell
$seed = '09923417857535490215'
& $py .\MultiServer.py "$rooms\AP_$seed.zip" --host 127.0.0.1 --port 38281
```

In a second PowerShell window:

```powershell
Set-Location D:\Archipelago
$py = '.\.venv-ot0\Scripts\python.exe'
$client = '.\worlds\octopath0\PythonSender\generated_room.py'
$seed = '09923417857535490215'
& $py $client --seed $seed inspect
```

Load save A before answering the in-game prompt. For each bridge prompt press **Ctrl+F3**, then **Ctrl+F7** in exploration. A fresh save should report `Binding status: absent`. Initialize it, save normally to slot A, reload A, and inspect again:

```powershell
& $py $client --seed $seed initialize
# Save to A and reload A in-game before running the next line.
& $py $client --seed $seed inspect
```

Expect `matched`, next index 0, both chest mappings and the Small Shield mapping. Stop server A with `/exit`. Set `$seed = '29768774052967974303'` **in both windows**, start server B using the same server command, and repeat the binding steps with save B. Keep both server saves between runs.

## Check both pairings

With server B running, perform the following sequence. Then stop server B, switch both windows back to seed A, start server A and repeat with the game slots reversed. Run the wrong-save chest test while Wishvale is still missing in that room.

| Order | Loaded save | Command in the client window | Expected result |
|---|---|---|---|
| 1 | Other room’s save | `& $py $client --seed $seed inspect` | Binding mismatch. The stored seed identifies the other room. |
| 2 | Other room’s save | `& $py $client --seed $seed check 70115` | The watch rejects the save at arming. Wishvale remains missing. |
| 3 | Matching save | `& $py $client --seed $seed check 70115` | Arm the watch and open Wishvale’s West Stump Chest. An already-open chest also counts. Expect `CONFIRMED 10070115.` |
| 4 | Other room’s save | `& $py $client --seed $seed deliver` | Authorization fails on binding mismatch. Shield count and saved index hold. |
| 5 | Matching save | `& $py $client --seed $seed deliver` | One Small Shield arrives at index 0. Expect next index 1. Disarm, save and reload. |
| 6 | Matching save | `& $py $client --seed $seed inspect` | Binding matches and next index is 1. Verify the one-shield increase persisted. |

Save to the matching slot before changing game slots if you want to preserve chest-opening progress. Press Ctrl+F3 after each delivery attempt. The two-room playtest passes when both directions match this table. Record each room’s seed name, bound slot, rejected operation, checked location and final shield delta.
