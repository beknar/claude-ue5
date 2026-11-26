# The list of 2026-11-22: the final report

The user's list ([improvements16.txt](improvements16.txt)) and its plan ([improvements16_plan.md](improvements16_plan.md)) were done in 28 phases, a pull request each (PRs #111 to #134 and this one). A general-purpose agent reviewed each PR; its finds were fixed and tested before the merge. This report says what was built, what was measured, and what could not be checked.

## What was built

| Phases | PR | What |
|---|---|---|
| 1 | #111 | The packaged game's frame rate in every city and biome (`-RDPerf`, fixed seeds, kept places; [performance.md](performance.md)'s BEFORE) |
| 2-3 | #112 | The loading cover; her summons on the wilds' and towns' maps; the wilds' ground in levels of detail |
| 4-5 | #114 | Nanite foliage in the wilds, Nanite in the cities |
| 6-7 | #113 | The cities' lights, people and dome by distance; their interiors batched by building and hidden unless seen |
| 8-17 | #115-#124 | The caves rebuilt with the Hyper Cave Building Toolkit: their own planner, the kit's dressing, materials, geodes and socket stones, weapons, armour and breath underwater, the charm slot and cursed relics, fossils, tablets and cave paintings, the caves' links with the wilds, gold and trade goods |
| 18-23 | #125-#130 | Heaven: street lights, modern signs and map symbols, the research tower; its streets (markings, signals, signs, parking); storeys, stairs and lifts; shops, services and containers; modern goods, pedestrians, neon and the city's sound; the traffic |
| 24 | #131 | The skyscrapers' level `heaven_tower` |
| 25 | #132 | The fortress's defenders (soldiers, medics who heal, drones, mechs, aliens) |
| 26 | #133 | The fortress's tiers 1 and 2 as an office building |
| 27 | #134 | The fortress's tiers 3 to 5 as an open alien world from the Alien Planet's baked clusters |
| 28 | this PR | AFTER in [performance.md](performance.md); the Shipping package with a full cook and its runs; two fixes the runs found; this report |

## Phase 28

### The package

`builds\list16final`: Shipping, full cook, 0 cook errors, 28.6 GB in 95 files. `package_mistward.ps1 -Test` ran 22 runs. All of these passed:
- the menu and the town;
- the castle and the catacombs;
- Vel Morrath, The War Engine and the sewers;
- Kethrys Spire's tower and Heaven's fortress, with the fortress's open tier (`fortress_open`: the sky up, 10,594 cluster parts placed);
- the caves;
- the horse, the village and the cave under a tower;
- the four other cities;
- the skyscraper (`tower`);
- the 45-minute walk in the wilds.

They peaked at 2.7 GB of memory on the menu and 5.2 to 6.5 GB in play, with no crash report.

Two runs failed, and both were fixed:
- **The console run**: its self-test typed "rd.Wild" for the Tab completion, which `rd.WildLod` (phase 3) had made ambiguous. It types "rd.WildR" now (`RD/RDConsole.cpp`).
- **The display run**: the game crashed. The castle applies `-RDApplyDisplay` in its BeginPlay, which runs inside the map's load. At that moment the movie player's loading screen (phase 2) still draws into the window's back buffer on its own thread. The resize under it crashed the D3D12 render pass: an access violation in `FD3D12CommandContext::SetRenderTargets`, while the main thread was in `FD3D12Viewport::Resize`. The stack was named with the build's PDB. The crash came and went: phase 8's package passed the run, while MID's (after phases 2 to 7) and phase 24's failed it, and list 15's package passed. It had first been blamed on a hidden PowerShell window. The apply now waits for the loading screen to finish (`RDMistward4.cpp`'s `TickDeferredDisplay16`). The rebuilt package passed the display run 3 times of 3 (1600 x 900 inside, the screen's 200 % scaling, saved, the least size 960 x 540), and the console run.

### AFTER

The same package and places as BEFORE (16016's seeds, BEFORE's places replayed), at 3840 x 2160, Epic quality, on the RTX 3060. Measured on 2026-11-25: 82 places in the wilds, then the two dungeon halls. Every place was measured but the canyon networks' run, which the run refuses as in BEFORE.
- **The worst places gained the most**: the temperate autumn forests 17.9 to 21.9 FPS (+22 %; the GPU 55 to 44.5 ms a frame), and the volcanoes 13.8 to 16.5 (+20 %).
- **The cities**: 24.5 to 33.8 FPS, from -3 % to +8 % against BEFORE (Heaven's square +8 %, Brokenspire's square at noon +6 %).
- **The biomes**: mostly within ±5 %. Below that: the wetlands standing -11 % (running -0 %), the plains -5 to -6 %, the geothermal caldera -5 to -6 %. These are the table's percentages, which drop the decimal: the wetlands' is -11.5, the castle's hall -7.5.
- **The halls**: the castle's first hall 34.7 FPS (-7 %), the fortress's 36.3 (+6 %).
- **Against MID** (the level-of-detail work alone, before phases 8 to 27's content), most places read the same or a few % lower. The largest falls are Ashenreach at midnight: its street 32.1 to 27.9 (-13 %) and its square 32.6 to 29.4 (-10 %). The fortress's hall rose 33.6 to 36.3 (+8 %).

The GPU is the limit nearly everywhere: 24 to 45 ms a frame against 4 to 20 ms on the game thread. The volcanoes' game thread is the exception, at 27 ms.

## What could not be checked

- **What a player sees and hears**: whether the caves, Heaven's streets and the alien world read as intended. The pictures in each phase's test show them; no person looked at them in play. The city's sounds and the neon's hum were chosen by name and measured, never heard.
- **Not played through**: a fight in the open alien tiers, their vaults' and arenas' force-field doors, and their ceiling traps; the fortress's defenders met in its rooms rather than spawned by the test. Also the tower level's empty offices, and saves made in it. All are in [TODO.md](../TODO.md).
- **The last build's other runs**: the console and display fixes were built after the 20 other runs passed, and only those two runs went on the rebuilt package.
- **One resolution**: the plan asked for BEFORE's two, but BEFORE settled on the desktop's own (1920 x 1080 read the same: the engine's screen percentage renders a 4K screen at about that).
- **The frame rate on other machines**: everything was measured on this one: a Ryzen 5 5600G, an RTX 3060 12 GB, 32 GB of memory, other programs open.
