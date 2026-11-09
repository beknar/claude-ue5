# Heaven and its fortress (`908`, `909`, `RD/RDHeaven.cpp`, the modern plan in `RD/RDTownPlan.cpp`, the theme in `RD/RDSection.cpp`; the user's list of 2026-11-08b, `docs/improvements9.txt`, its fourth phase; `docs/levels/heaven.md`)

The city is a wilderness town on `brokenspire` with the modern plan (`FRDWildTown::Plan` 5 -> the generator's `TownPlan`, `bModern`; `bMid` as the other cities: a landmark at the middle over a dungeon of its own); the fortress is `heaven_fortress`, a Save As copy of `mistward_castle` with its own `DungeonKey` ("heaven"). Every rule is behind `TownPlan == 5`, the `Modern*.` / `Lab.` / `Heaven.` pieces or a level's own data: the other towns and dungeons are unchanged.

## The city

- **A theme reskins a town by piece name**: the town section's `Theme` is "Heaven" for plan 5 (it is `NAME_None` for every other town), so `Pc` / `AddPiece` take "Heaven.<name>" wherever `908` made one: the wall's courses and the towers' cone roofs (`Heaven.Town.CityWall`, `Heaven.Town.CWall`, `Heaven.Town.TowerRoof`), the furniture (`Heaven.Desk`, `Heaven.Bookshelf`...). A direct `Generator->Piece(...)` is not themed: sizes read that way are the original's, so a reskin fills the original's box (`908`'s `refit` reads the original's adjusted bounds). `Bookshelf` and `CandleStand` are blueprint pieces (`ActorClass`, no mesh): a themed mesh replaces them all the same.
- **Pieces from boxes**: `908` merges cubes into meshes (`StaticMeshEditorSubsystem.merge_static_mesh_actors`, the pivot the world's origin, the physics data merged so each box keeps its collision). The merge puts "SM_" before the name it is given, and makes the mesh in memory only: save it (`884 heaven`'s third run found none after a restart: the level's pieces pointed at nothing). Build each in the frame of the piece it stands for (the house kit's walls about their line, the door's leaf along +Y from its hinge, the dungeon's walls through `907`'s normalisation).
- **What the town grows besides its grass**: the gardens' wheat (`Town.Crop2`, `SM_WheatGrass01`) stood in Heaven's streets after the short grass and the bushes were turned off; the homes' gardens, pens and cooking fires are off in Heaven (`TownLife`). Count what the test forbids by mesh name over the whole section.
- **Which way a merged car faces**: read it from the blueprint's parts, not a picture (the front doors stand at +Y, the rear doors at -Y: the front is +Y).
- **Traffic**: a car per lane every 45 m was 160 cars; every 70 m, 96. A car waits for her within 9 m ahead in its lane (measured: 6 m away, it stayed still 2.5 s and drove 30 m once she stepped aside).

## The fortress

- **A shot clip's "fastest bone" is late in a burst**: the trooper's and the commander's release came out 3.0 s; the release is held to 0.5 s.
- **A held shooter fires only within its range**: a trooper held 10 m from her (its range 9 m, `max_chase_speed` 1) fired nothing in 12 s; from 7 m it fired twice and both rounds reached her.
- **The start section keeps the castle's great-hall furniture**, as every dungeon copied from the castle.
