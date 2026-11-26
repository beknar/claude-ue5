# The list of 2026-11-26: the plan

The user's list is [improvements17.txt](improvements17.txt):

- the town squares' stands and shops tripled, each offering different goods at the town's tier;
- a loading screen that moves;
- the minimap's building outlines shimmering at 1080p;
- a second game mode, **Closed Structures**, beside today's **Immersive Interiors**;
- the frame rate with it, at 1080p and 4K, in every city and biome;
- the instructions on its last line.

This plan breaks the list into phases, each one PR. Each PR is built, tested with a step of its own in a level's scripted test, reviewed by an independent review agent, fixed, tested again and merged, in the order below. After the last PR the Shipping package is built and run.

An independent review of the first draft found 13 problems, and this version answers them:

- a building cannot be furnished again from its own seed;
- skipping the town's furnishing loses its spots and beds;
- a level trip at every door is too heavy;
- the looted state would split between the modes;
- Brokenspire's tier is read before the world exists;
- the market's goods ignore what her hero can use;
- buying at one tier and selling at another pays;
- F picks the first stand, not the nearest;
- the stands' draws move the lamps;
- the performance runs mix two changes;
- some tests measure a stand-in;
- the later phases are too large.

Conventions, as in list 16:

- Stages go under `949` (the building levels and the closed towns) and `950` (the markets).
- New C++ goes in `RD/RDList17*.cpp`, and a changed rule in its own file.
- Each feature has a named step with a stated measure in `884` (the towns), `888` (the wilds) or `868` (the castle and the dungeons).
- What is not built or not measured goes in `TODO.md`.
- CLAUDE.md's stage list and the rules files are updated where a phase changes what they say.

## What the code does now (the survey of 2026-11-26)

- **The squares' stalls are scenery.** Every city but Heaven has exactly 4 (`RDTownPlan.cpp` 1024-1032), each a `Town.Stall1-3` piece drawn from step 1's stream (2075) with a buyer's chat spot before it.
  - F does nothing at a stall: `TS_Stall` has no case in `TownInteract`.
  - Heaven skips them.
- **One stock for the whole town.** `TownStock()` (`RDTownGame.cpp` 498) offers potions, food, repair, torches, scrolls and unknown recipes up to the **game's** tier (`GetGameTier`, the deepest tier opened in any dungeon). Weapons, armour, rings, tomes and shields are never sold.
  - **Prices:** `PriceOf` scales used-up goods by the game's tier.
  - **Stores:** every city has one general store (`TK_Store`).
  - **Heaven:** up to 12 shops of 3 kinds (`ShopKind21`, `ShopSells21`).
  - **F's spots:** the spot loop takes the first spot in reach, not the nearest (`RDTownGame.cpp` 1538).
- **A town's tier:** the wilds' chain (`MakeTierChain`: Brokenspire 1, Vel Morrath 5, Ashenreach 10, Graymourne 15, Kethrys Spire 20, Heaven 25). Brokenspire, the home section, is built before the world is ready.
- **Loading:** two paths share one static widget (`RDCover16Widget()`, `RDList16b.cpp` 33).
  - The movie player's loading screen, painted on its own thread during `LoadMap` (a package's only: play in the editor has none).
  - The in-game cover after a level opens, a travel, a teleport or a respawn.
- **The minimaps** (`RDTownHUD.cpp` 188, `RDWildHUD.cpp` 284, `RDHUD.cpp` 1241) draw at `C + (W - Her) * K`, with her raw place and no rounding.
  - The town's walls are 1.6 px Canvas lines at 1080p, which are not anti-aliased: as the offset slides by fractions of a pixel a line covers one row, then two.
  - Its tiles are translucent boxes overlapping by half a pixel.
  - The wilds' minimap draws no building outlines. Its ground picture is resampled on a grid anchored to her place.
- **Buildings and interiors:**
  - **The shell:** a town building is a shell (`TownShellBuilding`) with one door (`TownBlds[BI].Door`).
  - **Furnishing:** it is furnished from the town's shared plan stream, building by building (`TownFurnish(GenR, ...)`, `RDSection.cpp` 2166). The furnishing also makes the service spots, the beds and the blocked tiles that people's posts, sleep and paths use.
  - **Hiding:** its interior is batched per building (`TownBldIsm16`) and hidden unless seen (`TickTownInteriors16`).
  - **Windows:** they are recorded (`TownWindows16`).
  - **The wilds:** houses (`FitWildHouse`) and farmstead buildings (`WildKitBuilding`) are furnished from their chunks' draws.
- **The precedent:** Heaven's skyscrapers (`RDTower24.cpp`) travel to a level of their own (`heaven_tower`) and back with a load that rebuilds the whole city.
  - **The outside view:** the city is captured round the tower into cube maps, and an unlit material (`M_HT24_View`) shows it in the windows.
- **Options** live on the Escape menu's Options page, kept in `GameUserSettings.ini` (`RDMistward4.cpp`).
- **Performance:** `-RDPerf` and `perf_mistward.ps1` measure every city's square and street at noon and midnight, and each biome standing and running.
  - Only the 3840 x 2160 places file exists.
  - The script passes no extra switch to the game.

## Readings of the list

- **"3x more stands and shops, each one different in what they offer":**
  - **Stands:** every city's square gets **12 stands** where it had 4. Heaven had none, and gets 12 modern kiosks and carts.
  - **Working stands:** each stand has a keeper behind it, and F at the stand or the keeper opens its store.
  - **Twelve trades** (`SourceArt/list17/stalls17.json`), one each, none shared on a square, with a medieval and a modern name:
    - weapons;
    - armour;
    - shields and off-hands;
    - rings and charms;
    - potions;
    - food and meals;
    - scrolls;
    - tomes and manuals;
    - herbs and reagents;
    - crafting materials and repair items;
    - torches, oil and tools;
    - gems, socket stones and trade goods.
  - **Shops:** every medieval city's one general store becomes **three stores**: general goods, an outfitter for weapons, armour and shields, and an apothecary for potions, herbs and scrolls.
  - **Heaven's shops:** Heaven's 3 shop kinds become **9**: grocery, pharmacy, hardware, electronics, jeweller, bookshop, sporting goods, outdoor outfitter, herbalist. Its shop buildings are not tripled.
- **"Items of the same Tier that the town is in":** a town's tier is one helper over the chain's table by the town's name (`TownTier17`: 1, 5, 10, 15, 20, 25), so Brokenspire has its tier before the world is made.
  - **What is offered:** each item at the 5-tier band holding the town's tier (`RDReachedTier`), and the gear whose `Tiers` hold it (or the nearest below).
  - **What her hero can use:** filtered as every other offer is:
    - weapons by `WeaponFits`;
    - armour by `Fits` and `Wears`;
    - tomes by `Learns`;
    - scrolls by `ScrollTypes`.
  - **What is never offered:** the weight-0 named rings, the caves' own items (`CaveItemAllowed16`), recipes she cannot learn. Heaven's twins are swapped in.
  - **One tier for both ways:** a square's seller buys and sells at the town's tier, so nothing bought cheap in a low town sells dear at the game's tier there. `PriceOf` elsewhere is unchanged.
  - **Other services:** the healer, smith, temple and inn keep their rules.
- **"The loading screen needs to show some animation and movement":** the shared widget is a Slate widget of our own that paints itself from real time (`FPlatformTime`):
  - a ring of runes turning round a breathing emblem;
  - a bar of light running under "Loading";
  - a tip changing every few seconds.
  - It reads only the clock and constant text, so it may paint on the movie player's thread during `LoadMap`.
  - The in-game cover moves once a game frame, so a slow frame while a town is built shows as a hitch, which is measured.
  - `rd.LoadingCover 2` keeps the plain board for comparison.
- **"In full screen 1080p, the mini-map's building outlines shimmer when the character is moving":**
  - **Snapping:** every minimap's base (where the world's origin lands on the screen) is rounded to whole pixels, and each point is that base plus its own fixed fraction. The drawing then moves a whole pixel at a time and keeps its shape.
  - **Line widths:** lines are whole pixels thick.
  - **Comparison:** `rd.MinimapSnap 0` brings back the old drawing.
  - **The wilds' ground picture:** it is made on a grid fixed to the world and drawn round its own point. This is a second fix of the same kind, not the outlines' fix.
- **The game mode:** the Options page gets **Structures: Immersive Interiors / Closed Structures**, with the selected mode's description under it.
  - **Storage:** it is kept in `GameUserSettings.ini` and overridden by `-RDStructures=closed|immersive`, read once into the game instance.
  - **Applying a change:** an autosave and a load, which builds the town or the wilds round her again in the new mode at the same place.
  - **Immersive Interiors** is today's game.
  - **Closed Structures:**
    - **The town:** every enterable building is a closed shell. Its interior is not built: no furniture instances, interior lights or hearths' fires.
    - **Its windows:** they show pictures of its rooms.
    - **Entering:** opening its outer door opens a level of its own for that building, a level instance (`ULevelStreamingDynamic::LoadLevelInstance` of the small map `town_building`) streamed in where the building stands.
    - **Its contents:** the building's furniture and lights are spawned into that level from the data its town recorded.
    - **While she is inside:** the town and the wilds round it are hidden (not drawn), and the windows show the outside as captured as she came in.
    - **Leaving:** going out through the door unloads the level and shows the town again.
- **One furnishing, two ways of drawing it:** the town is planned and furnished the same way in both modes: every draw, spot, bed, blocked tile and container in its place.
  - **The record:** in Closed Structures the static furnishing of an enterable building is recorded per building as data instead of being drawn: each piece's name, transform, material and collision, and its lights and fires. The building's level spawns exactly those pieces.
  - **What stays in the town:** the containers, doors and people are the town's own actors in both modes, shown only while she is inside the building. A container looted in either mode is looted in the other: one index, one key.
  - **The wilds:** houses record their chunk-drawn furniture the same way.
- **People inside:** the townsfolk live their day in the town in both modes. Whoever stands inside the building's rectangle is drawn while she is inside: its keeper at work, its sleepers in their beds, a resident who walked in. Anyone else is not drawn. No one is moved between levels, so the day's rules, the services and F are unchanged.
- **"All buildings":** every city building with a door she can open, and in phase 8 the wilds' village houses, lone houses and farmstead buildings.
  - **Not included:**
    - the castle, the cathedral, the foundry, the spire and Kratos Aurorim Research (the dungeons' entrances);
    - Heaven's skyscrapers (a level of their own already);
    - burned and boarded houses;
    - camps and ruins.
- **Windows from outside ("a solid or glowing texture depicting the inside of that room"):** each lived-in window of a closed building gets an unlit pane in its frame (`TownWindows16`).
  - **What it shows:** a picture of a room of that building's kind and style, glowing at night while its lights burn.
  - **Making the pictures:** they are the game's own rooms, photographed by a test step in Immersive mode from outside each kind of window, and imported by `949 rooms`.
  - **Fallback:** a kind with no picture taken gets one painted by the local FLUX server, and the report says which.
- **Windows from inside ("depicting the outside of that building"):** as she enters, the town and the wilds round the building are captured into a cube map with the building's own pieces taken out (`CaptureTowerViews24`'s way). The building level's panes sample it by the view's direction (`M_HT24_View`).
- **"Describe both game modes":** the Options page's description line, and `docs/game-modes.md`, linked from the README and the player's guide.
- **The measures:**
  - **The runs:** `perf_mistward.ps1 -Extra` passes switches to the game. Four runs on the same package, all replaying the 3840 x 2160 places file:
    - Closed Structures at 1920 x 1080 and at 3840 x 2160, as the list asks;
    - Immersive Interiors at the same two, so each change is read against the same build, markets included.
  - **Render resolution:** each table records the render resolution (the screen percentage).
  - **The section:** **Closed Structures** in `docs/performance.md` has both resolutions with the Immersive column beside.
  - **Inside buildings:** a leg measures three building levels (a tavern, a home, a Heaven office).
  - **Expectations:** interiors are already hidden unless seen, so the difference in the streets may be small. The report says what was measured, not what was hoped.
  - **Time:** each run is long, about 4 hours, so they run back to back unattended.

## The phases (one PR each, in this order)

1. **The plan** (this file), reviewed, merged.

2. **The loading screen and the minimaps** (`RD/RDList17.cpp`, `RDList16b.cpp`, `RDTownHUD.cpp`, `RDWildHUD.cpp`, `RDWildMap.cpp`, `RDHUD.cpp`).
   - **The loading screen:** the widget counts its paints and the distinct ring phases it drew between `PreLoadMap` and the end of the load, and logs them (`RDLOADING17`).
     - The package's console run reads that line: during a real `LoadMap`, more than 10 paints and more than 10 distinct phases.
     - **Test `888 loading17 -Light`:** two pictures of the in-game cover half a second apart differ inside the ring's box and not elsewhere, and the widget's paint count rises between them.
   - **The minimap:** recorded on the HUD: each drawn wall line's start and thickness.
     - **Test `884 minimap17 -Light`:** in a 1920 x 1080 window, play paused, she is stepped 0.1 px at a time across the square. Every recorded line's start keeps its sub-pixel fraction, its thickness is whole, and a picture at two whole-pixel offsets is the same picture shifted.
     - **The comparison:** `rd.MinimapSnap 0`, where the fractions slide.
     - **The package:** the console run at 1920 x 1080 full screen takes its pictures.

3. **The square's stands** (`RD/RDList17b.cpp`, `RDTownPlan.cpp`'s stall loop, `950 stalls`, `SourceArt/list17/stalls17.json`).
   - **Layout:** 12 stands in rows on the square's long sides, kept off the well, the board, the lamps and each city's centrepieces by their tiles.
   - **Streams:** every stand's mesh and trade come from a hash of the town's seed and the stand's place; the plan's streams are not touched (step 1's lamps keep their turns).
   - **Heaven:** kiosks and carts from Heaven's pieces (`950 stalls`).
   - **Keepers:** each stand has a keeper (a Trader with `StallKind17`), who sleeps at night like a trader and wakes to serve as keepers do (`RDTServes`).
   - **F:** the nearest spot in reach takes it.
   - **Tier:** `TownTier17`, and the square sellers' stock and prices as in the readings.
   - **Test `884 stalls17 -Light` in all six cities, with two heroes (the Warrior and the Mage):**
     - 12 stands, each with its keeper;
     - each stand opens from where a player stands before it, and sells only its trade, none shared;
     - every item at the town's band and fit for the hero;
     - prices the same bought and sold at the town's tier, with the game's tier set both under and over it;
     - the town's buildings, containers and step-1 pieces (lamps and carts) in the same places with the switch off (`rd.Stalls17 0`).
   - `check_town`'s 4 stalls become 12.

4. **The square's shops** (`RD/RDList17c.cpp`, `RDTownPlan.cpp`'s trades, `950 shops`).
   - **Medieval cities:** two more stores beside the general store, placed by a stream of their own after every other building (so no earlier building moves), each with its trader, counter, sign and trade.
   - **Heaven:** 9 shop kinds, with their signs and stocks.
   - **Test `884 shops17 -Light` in all six cities:**
     - three stores in each medieval city, each selling only its trade at the town's tier;
     - Heaven's nine kinds;
     - the earlier buildings and containers unchanged;
     - `884 heaven21_shops` updated.

5. **The building level, its build and its door** (`949 level`: the small map `town_building`, an empty level with no lights of its own; `RD/RDBuilding17.cpp`).
   - **The record:** a town built with the record switch keeps, per enterable building, its static furnishing as data (`FRDBldRecord17`): pieces, lights and fires, with the furnishing's draws unchanged.
   - **Entering:** `EnterBuilding17(BI)`, also the console's `rd.EnterBuilding`:
     - the outside is captured into a cube (the building's own pieces taken out);
     - the level instance is streamed in at the building's place and the record spawned into it;
     - the town's other pieces and the wilds' chunks are hidden, and the building's people, containers and doors shown;
     - the inside panes sample the cube.
   - **Leaving:** the door inside is the way out; the level is unloaded and the town shown again.
   - **Test `884 building17 -Light`:** a home, a tavern and a store entered from Brokenspire and from Vel Morrath:
     - the level is loaded, and the pieces spawned match the record's count;
     - the furniture stands where Immersive's stood (each piece's transform against the Immersive build of the same seed, within 1 cm);
     - she walks inside;
     - the panes' view against a capture taken at the same place, 0.9 or more alike;
     - out through the door, the level is gone, the town is drawn and she stands at the door;
     - the time from F to inside and back is measured.
   - **The package:** `town_building` is named to the cook, and `869` run for the panes' material.

6. **People, services, containers, saves and the mode** (`RD/RDList17d.cpp`).
   - **The option:** the Options line, its description, the ini key, `-RDStructures`, applied by an autosave and a load.
   - **The closed town:** recorded instead of drawn; the door's F says "enter".
   - **Inside:** the people inside are drawn and served there (the keeper's store, the inn's bed, the healer, the bank's stash).
   - **Saving:** a save inside is a save at its door outside; a load in Closed mode never puts her inside.
   - **Containers:** opened inside and kept by their town indices in both modes.
   - **Test `884 closed17 -Light` in all six cities:**
     - no furniture instances or interior lights in the closed town;
     - the same spots, beds and containers as Immersive at the same seed;
     - F at a door enters and the services work inside;
     - a chest looted in Closed is looted in Immersive and back;
     - the option's line and description in both modes;
     - a save made inside loads at the door.

7. **The windows' pictures from outside** (`949 rooms`, `949 panes`).
   - **The pictures:** taken by `884 rooms17` in Immersive mode, one or more per building kind and style, imported as textures, and given to the panes by kind.
   - **Night:** the panes glow while the building's lights burn.
   - **Description:** `docs/game-modes.md` is written here.
   - **Test `884 panes17 -Light`:**
     - every lived-in window of a closed building has a pane, and none of an open one;
     - a pane's picture is its building's kind;
     - lit at night and dark when its people sleep, read in pictures where the pane is on the screen (`project_world_to_screen`);
     - the square's frame rate at noon and midnight, closed against immersive, in one session.

8. **Closed Structures in the wilds** (`RD/RDList17e.cpp`).
   - **The houses:** village houses, lone houses and farmstead buildings record their chunk-drawn furniture and lights as data (their draws unchanged), and enter the same building level.
   - **Their people and containers:** households and containers stay the chunks' own, shown while she is inside.
   - **Test `888 closed17 -Light`:** a village house and a farmhouse entered and left, their furniture against Immersive's, their containers kept, their panes counted.

9. **The package, the measures and the report.**
   - **The package:** Shipping with a full cook, run with `-Test`. A `closed` run (a city in Closed Structures, a door entered and left) joins the others.
   - **The measures:** the four performance runs, and `perf_doc.py` writes **Closed Structures**.
   - **The report:** `docs/improvements17_report.md`, with `TODO.md` updated.
   - **The binary:** once this PR is merged, the Shipping binary is built again from `main` and its console run passes.

## Order and parallel work

- **Order:** phases 2 to 4 are small and independent of 5 to 8, and come first: 5 to 8 close the town they change.
- **One editor at a time:** only one editor may run on the project, so builds and tests are serial.
- **What runs alongside:**
  - each PR's review agent runs while the next PR is coded;
  - the room pictures (phase 7) are taken in the editor session that tests phase 6;
  - the report and documents are written while the package cooks and the performance runs go.
