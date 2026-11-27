# The game's two modes for buildings

Chosen on the Escape menu's Options page, the **Structures** line (the user's list of 2026-11-26, `docs/improvements17.txt`; its plan
`docs/improvements17_plan.md`). The line below it says what the chosen mode is. The choice is kept with the other options
(`GameUserSettings.ini`, `[RandomDungeon.Options] Structures`); `-RDStructures=closed|immersive` on the command line sets it for one
session. Changed in a town, it is applied at once: the game is saved and loaded where she stands, and the town is built again round her
in the new mode. Everything else stays as it was: the town's seed, its buildings, containers and people, what she has looted.

## Immersive Interiors (the default)

> Every building has its rooms in the town: walk in at its door, see in at its windows.

- Every building is built whole in the town: its walls, rooms, furniture, lights and people, all part of one level.
- Her doors open onto the rooms behind them. Walking in or out is just walking.
- Seen from the street, a window shows the room behind it, lit by the room's own lamps.
- The town hides the inside of a building unless she is in it or can see into it, by its door or a window (list 16's seventh phase:
  `rd.InteriorHide`).

## Closed Structures

> Each building a closed shell; its door opens a level of its own. Windows show pictures.

- The town draws each building as a closed shell: its walls, roof, door and windows. Its furniture is recorded when the town is built,
  but not drawn in the town (`RD/RDBuilding17.cpp`). The buildings, their containers and the places of work, beds and stalls are the same
  as in Immersive Interiors.
- **Its door opens a level of its own.** F at a building's door streams in the building level (`town_building`) at the building's place,
  lays its recorded furniture, lights and containers in it, and puts her inside the door. The town's people who live or work there are
  inside with her: the innkeeper behind the bar, the trader at the counter, sleepers in their beds. Containers looted inside stay looted
  in either mode.
- **From inside, its windows show the outside.** Each window holds a picture of the street taken from that window as she comes in.
- **From outside, its windows show a room.** Each window holds a picture of a room of its building's kind and city: a home, a tavern, a
  smithy, a store, a chapel... in Brokenspire's, Vel Morrath's, Ashenreach's, Kethrys Spire's and Heaven's looks. There are 55 pictures,
  taken from inside the game's own furnished rooms (`884 rooms17`, imported by `949 rooms`: `RD/RDList17e.cpp`). At night a window
  glows while someone awake is inside, as the buildings' lights do in Immersive Interiors. By day it is dim.
- **In the wilds.** A village or lone house and a farmstead's farmhouse, barn, shed, coop or granary are closed the same way: their furniture and lamp are laid in the building level as she walks in through the door F opens, and let go as she walks out (`RD/RDList17f.cpp`). A farm building's windows show a room of its kind; the village houses, the packs' own meshes, have none.
- **Leaving.** She walks out through the door, or F at the door, and the building's level is let go. A save made inside a building is
  a save at its door's outside, facing out of it.
- **Why choose it.** There is less to draw in a town: no furniture, lights or people of hidden rooms, and one picture per window. The
  frame rates in every city and biome, at 1080p and 4K, are in `docs/performance.md`'s "Closed Structures" section.
