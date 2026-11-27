# The list of 2026-11-26: the final report

The user's list ([improvements17.txt](improvements17.txt)) and its plan ([improvements17_plan.md](improvements17_plan.md)) were done in nine phases, each a pull request (#137 to #144, and this one). A general-purpose agent reviewed each PR; its finds were fixed and tested before the merge. This report says what was built, what was measured, and what could not be checked.

## What was built

| Phase | PR | What |
|---|---|---|
| 1 | #137 | The plan |
| 2 | #138 | The loading screen moves (a ring of runes, a bar, tips, painted from the real clock); the minimaps drawn on whole pixels (the building outlines no longer shimmer as she moves) |
| 3 | #139 | Every city square's twelve stands (three times the four of before), each a trade of its own, selling the town's own tier |
| 4 | #140 | Every medieval city's three stores and Heaven's nine shop kinds, each with its own stock |
| 5 | #141 | Closed Structures: each enterable building's furnishing recorded instead of drawn in the town; its door opens `town_building`, a level of its own laid with it; its windows from inside show the street (a cube captured as she comes in) |
| 6 | #142 | The Options page's Structures line (Immersive Interiors / Closed Structures) with a line describing the chosen mode, kept in `GameUserSettings.ini`; applied at once in a town by a save and a load; a save made inside a building loads at its door |
| 7 | #143 | The closed buildings' windows from outside: a picture of a room of their kind and city (55 pictures of the game's own rooms), glowing at night while the building's lights burn; [game-modes.md](game-modes.md) describes both modes |
| 8 | #144 | Closed Structures in the wilds: the village and lone houses and the farmsteads' buildings, their furniture and lamp laid in the building level as she walks in; the farm buildings' window panes |
| 9 | this PR | The Shipping package with a full cook and its runs (a `closed` run added); the frame rates in both modes at 1080p and 4K ([performance.md](performance.md)'s "Closed Structures"); this report |

## The list, item by item

- **"The town squares in every city need 3x more stands and shops, each one different in what they offer ... of the same Tier that the town is in"**: twelve stands a square (four before), each a different trade (`RD/RDList17b.cpp`), and three stores a medieval city (one before) and nine shop kinds in Heaven (`RD/RDList17c.cpp`). The stands sell items of the town's own tier, or the nearest tier below where a kind has none (`884 stalls17`, `shops17`). Every price is the one `PriceOf` gives everywhere.
- **"Loading screen needs to show some animation and movement"**: the loading board turns a ring of runes, fills a bar and changes its tips by the real clock (`RD/RDList17.cpp`). Measured under the loading cover in play (`888 loading17`: paints in distinct phases). In a packaged game's map load the board is drawn on the movie player's thread and logged; it was not looked at there (see below).
- **"In full screen 1080p, the mini-map's building outlines shimmer when the character is moving"**: the town's, the wilds' and the tactical minimaps are drawn on whole pixels, about a base that moves by whole pixels (`rd.MinimapSnap`). Measured by the pictures of two frames shifted by her move: their difference after the shift (`884 minimap17`, `888 minimap17w`).
- **"Immersive Interiors" and "Closed Structures" behind the Options button, both described**: the Options page's Structures line and its words (`RD/RDList17d.cpp`, `884 closed17`). [game-modes.md](game-modes.md) describes both modes.
- **"All buildings their own level, where opening a door opens a new level just for that building"**: every enterable building of the six cities (`RD/RDBuilding17.cpp`, `884 building17`, `closed17`) and the wilds' houses and farm buildings (`RD/RDList17f.cpp`, `888 closed17w`). Not enterable as their own level: the castle and the cities' landmark halls (the dungeons' ways in), Heaven's skyscrapers (a level of their own already), burned and boarded houses.
- **"For this new mode, the windows show a solid or glowing texture depicting the inside of that room"**: a picture of a room of the building's kind and city at each window, glowing at night (`RD/RDList17e.cpp`, `884 rooms17`, `panes17`). Each picture shows a room of the same kind, not that building's own room.
- **"When looking outside a window, show a solid or glowing texture depicting the outside of that building"**: a cube of the street captured just inside each window as she comes in, shown on a pane there (`884 building17`: the windows' views against the street, 0.52 to 0.94 alike).
- **"With this new mode enabled, at 1080p and 4K full screen, measure FPS in all the cities and in the wilderness in all biomes"**: [performance.md](performance.md)'s "Closed Structures", both modes side by side at both resolutions.

## Phase 9

### The package

`builds\list17`: Shipping, full cook (11,908 packages), 28.0 GB in 96 files. `package_mistward.ps1 -Test` ran 22 runs, and 21 passed at once: the menu, the town, the castle, the catacombs, Vel Morrath, the four cities' dungeons, the caves, the horse, a village, a tower's cave, Ashenreach, Graymourne, Kethrys Spire, Heaven, a skyscraper, the display settings, the console, and the new `closed` run. In the `closed` run Brokenspire was built in Closed Structures and F at the store's door took her in. Its level was laid round her with 12 pieces and 21 window panes. No run left a crash report. The peak memory was 7,158 MB, in the `closed` run.

`fortress_open` failed on its first try. It reached the open tier with every one of its 10,733 parts placed, but its mark read `sky=0.99`. The game writes that mark once the sky reaches 0.99, while the script's pattern asked for 1.00. The pattern now follows the game's threshold, and the run was repeated: it passed with `sky=1.00` and 11,358 parts placed.

### The frame rates

The Shipping package was run full screen at 1920x1080 and at 3840x2160, once in each mode, over the same 82 places: each city's square and a street at noon and at midnight, and a 30 s run in each biome ([performance.md](performance.md)'s "Closed Structures"). One place, the canyon networks' run, was skipped in all four runs, because the game moved her 13 km in one frame there. It was skipped the same way in the page's earlier sections.

| | Immersive Interiors | Closed Structures | Change |
|---|---|---|---|
| 1920x1080, all 81 places | 28.4 FPS | 29.0 FPS | +2 % |
| 1920x1080, the cities' squares and streets | 27.8 FPS | 29.2 FPS | +5 % |
| 3840x2160, all 81 places | 29.0 FPS | 28.6 FPS | -1 % |
| 3840x2160, the cities' squares and streets | 29.3 FPS | 28.4 FPS | -3 % |

These runs do not show Closed Structures to be clearly faster or slower. The averages differ by 1 to 5 %, and in opposite directions at the two resolutions. Within 3 % of each other were 70 of the 81 places at 4K and 54 at 1080p. The two resolutions read almost alike, as they do in the page's earlier sections: the game's resolution quality group is 0, so 4K is not drawn at four times the pixels.

The order of the runs may account for much of the difference. Both Closed runs came first (20:01 and 20:53) and both Immersive runs after (21:45 and 22:37). At 1080p Closed was faster at 53 places and slower at 14; at 4K it was slower at 47 and faster at 20. Changes that lean one way like that look like the machine changing over the evening (its heat, its background load) more than the mode. One run per mode cannot tell those apart.

Single places differ by more:
- **Heaven** disagrees between the resolutions. At 1080p Closed was 4 to 13 % faster at its four places. At 4K it was 15 to 35 % slower at three of them. At the street at midnight, Immersive's 36.8 is above every earlier section's figure there (29.4 to 30.7), so the outlier may be the Immersive run.
- **Vel Morrath's street at noon** was 24 % faster in Closed at 4K and 10 % at 1080p.
- **The tundras' run** was 12 % slower in Closed at 1080p and 6 % at 4K.

[TODO.md](../TODO.md) holds a repeat with the modes in alternating order.

### What was not checked

- **The loading board in a real map load**: during a packaged game's `LoadMap` the board is painted on the movie player's thread. Only the log says it was painted, and the Shipping package writes no log. It was not seen in a Development package.
- **Sound**: nothing new makes a sound.
- **The listed limits**: [TODO.md](../TODO.md)'s section for this list holds the limits found on the way and the parts written but not tested. Among them:
  - the village houses have no window panes;
  - the window pictures show a room of the building's kind, not its own room;
  - a mode chosen out in the wilds is applied by a save and a load, which no test ran;
  - walking from one closed building straight into its neighbour was not tested.
