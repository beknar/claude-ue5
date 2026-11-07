---
paths:
  - "claude_ue5/Source/claude_ue5/RD/RDHoly*"
  - "claude_ue5/Source/claude_ue5/RD/RDTownPlan*"
  - "claude_ue5/Source/claude_ue5/RD/RDSection*"
  - "pipeline/unreal/891_*"
  - "pipeline/unreal/892_*"
  - "claude_ue5/SourceArt/vel_morrath/**"
  - "docs/levels/vel_morrath.md"
---

# Vel Morrath and its catacombs (`891`, `892`, `RD/RDHoly.cpp`, the holy plan in `RD/RDTownPlan.cpp`, the floors in `RD/RDSection.cpp`; the user's spec of 2026-11-06, `docs/vel_morrath.txt`, `docs/levels/vel_morrath.md`)

The city is a wilderness town on `brokenspire` with the holy plan (`FRDWildTown::Plan` 1 -> the generator's `TownPlan`, its size `Tiles` 168); the catacombs are `vel_morrath`, a Save As copy of `mistward_castle` with `bTierFloors` and its own `DungeonKey`. Every rule is behind `TownPlan == 1`, `bTierFloors` or a non-empty `DungeonKey`: Brokenspire, the other towns, the castle and the older dungeons are unchanged.

## The city

- **One level, several towns' data**: townsfolk and quests carry a `Town` (`FRDTownsfolkDef::Town`, `FRDQuestDef::Town`): a town uses its own defs for the roles it has and the shared ones for the rest; a quest is offered only in its town. `882` keeps the entries that have a town and the pieces outside "Town." (the city's are "Holy.*" and "Cathedral.*"), so `882` / `886` / `890` leave the city as it was: `892` needs running again only when its own pieces or `city.json` change.
- **A pack's piece by name is not what it shows**: the cathedral's rose window (Crownfall's) drew a black 7 m slab; it is out of `892`. Look at the cathedral in a picture in play after changing a piece.
- **A dry run that ends with her on the stair goes down for real**: `884 holy` moves her off the stair before it clears `travel_dry_run` (the next tick opened a level that did not exist yet: "ObjectInstance is null").
- **Measure the frame rate after the city has settled**: just after it was built round her the plaza read 5 a second, settled 24 (Brokenspire's square 15 to 30 in the same session); nothing hidden (lights, packs, people, effects) moved it by more than 4.

## The catacombs' floors

- **A set's floor is its actor's height** (`SpawnSection` at `SectionFloorZ`): everything placed in a set must go through the set (`TileWorld`, `GetRoomCenter`, `ShellCorners`, the vaults, `AddTrapAt`, the census' root, `PortalNeighbour`) or the generator's `TileCenter`, never a literal z 0. A position made from a room's 2D box (`RoomBox`: its centre, quadrants, wall slots, the corners and the wall anchors of `Furnish` and `LightRoom`) takes the set's height (`GetActorLocation().Z`): PR #23's review found them at z 0, 4.5 m a tier over the floor, and the first test had passed (it cleared the sets by script and traced floors only). `868 catacombs` measures every container, light and monster of a deeper set against its floor. The furniture test in `AddPiece` is relative to the set (`Z - actor Z < 30`).
- **The stairs keep the plan's draws**: the edge rooms are pushed in after their size and place are drawn (a portal block's room on a stair side keeps `StairTiles` of hallway before the border), and a stair tile draws its floor's and ceiling's turns as a flat tile does.
- **A stair is a ramp, not steps**: floor and ceiling tiles pitched toward the border (21 degrees at 4.5 m over 4 tiles of 3 m) and stretched by 1 / cos; the side walls stacked from the ramp's low edge to its high edge's ceiling. The walk test (`868 catacombs`) walks her up and down with `add_movement_input`: 5.3 s each way, never off the ground.
- **Trace a deeper set from just over its floor**: a trace from 6 m up stops on the ceiling of a set below the city's level (the first test read every tier-2 floor at +50, its ceiling). `floor_z(..., top=want + 150)`.
- **A test that walks a hallway opens its doors first** (`PushDoor`): the room's door between the hallway and the room stopped the first walk dead.
- **The dungeon's reveal is cyan over the whole picture** (a post-process wave from where she stands over a new set, `StartReveal`): a set generated round her in a test tints her, the bars, the minimap and every seam (the void behind them black). Not the depth, not the fog: picture a set after the wave.
- **The safety net's floor is her set's** (`FloorZAt`: the set's height, the ramp's on a stair), or a fall on a deep tier would never be caught and a walk on a stair could be.

## Between the city and the catacombs

- **The way down** (`EnterCatacombs`): the autosave, her state carried (`SaveCarry`), the way back kept (`ReturnAt` 7 m before the cathedral's door, `ReturnYaw`, `ReturnTown`), the store swapped to Brokenspire's state (the level always comes back as Brokenspire), then `OpenLevel(CatacombsLevel)` with her hero.
- **The way back** is a load into the wilds: `Arrive` "save" with `LoadAt` = `ReturnAt` and `bLoadPending`, so `TickWildLoad` builds the city round her (it measured 0.0 m from `ReturnAt`, 2.5 m from the cathedral's door). The labels name `WayBackName()` (the game instance's `ReturnTown`), not the generator's `TownName` (Brokenspire's on every copy of the castle).
- **Each dungeon's state under its key**: `URDGameInstance::Dungeons` (tiers, start loot), the counters through `DungeonCounterName` (the game instance's `DungeonCounter`: one format; "vel_morrath:tier", ":kills", ":boss", ":enter"); `GetGameTier` (prices) takes the deepest over every dungeon, but a quest's tier goal reads its own dungeon's tiers (`DungeonTierReached`: "tier" the castle's, "<key>:tier" that dungeon's).
- **One level, several towns' quests**: a giver's mark (the map's seals, the minimap, over their heads) goes by role, so it reads only the quests of the town she is in (`GetQuestLinesHere`, `IsQuestHere`).
- **One trip down** (`TravelToDungeon`: the forced autosave, her state, the town's state put away, the level): the Mistgate and the stair both call it.
- **The packaged game** (`package_mistward.ps1`, 2026-11-06): `vel_morrath` is named to the cook; its test goes down from Brokenspire with `-RDTownGo=catacombs` (`DescendToCatacombs`, the stair's own way; back to where she stood) and out to the city with `-RDTownGo=town:velmorrath` (the map's fast travel). The city's church, cemetery, relics and statue materials lacked the instanced-mesh usage (`869` now reads `vel_morrath`'s pieces and sets it): play in the editor drew them, a package would have drawn them grey.
- **The editor ran out of GPU memory** loading brokenspire after a long session (D3D12 `E_OUTOFMEMORY`, the editor then deaf to remote Python): restart it on the level the next test plays. On 2026-11-07 it did so twice in a row from a fresh start, at the first seconds of play on `brokenspire` (the editor itself holds about 5 GB of the 12 before play; the NVIDIA overlay and another program held 2.7); the third start ran `holy` and `descend` after the user closed programs using the GPU. Ask before a third try.
