---
paths:
  - "claude_ue5/Source/claude_ue5/RD/RDCave16.cpp"
  - "pipeline/unreal/945_caves16.py"
---
# The caves rebuilt with the Hyper kit (`945`, `RD/RDCave16.cpp`; the list of 2026-11-22, `docs/improvements16.txt`, phases 8 and 9; `docs/levels/caves.md`)

The cave level (`caves`) with the generator's `bCave16`: `Plan` hands the set to `PlanCave16` (the kit's rooms, tunnels between their openings, portals to the borders), the shell is `CaveShell16` (the kit's meshes, built in play only), `Furnish` is `CaveFurnish16`. Everything the game reads stays tiles (`Type`, `Owner`, `Rooms`, `CaveZ16`).

- **Measure the kit's pieces before laying them**: its rooms are open at the top, its tunnels are walls and a roof with a partial floor (the example map stands them on a stretched cube), its caps close a room's unused openings (on the opening's arrow), a tunnel leaves an opening along its arrow. `945 study` / `measure` read them; trace a mesh from inside its cavity (from above a tunnel's roof the ray meets the roof's back).
- **A tunnel is a wall**: it splits the set. Joins before portals; refuse any laid line that cuts another tunnel's mesh, a room's box it does not join, a cap's ground, or bends tighter than its half-width; try again rather than shrink a keep-out (shrunk, tunnels ran inside each other).
- **A bent kit mesh folds**: the small tunnel (2 to 3 m walkable) closed up on every bend and is drawn by none; round corners to twice the half-width.
- **Tiles meet only through openings**: a tunnel's tiles touch its rooms' only along the opening's own line (a 4-joined chain 6 m in to 6 m out); beside the opening the wall stands (a path there held her on a ledge), and a distance rule refused every tile of a diagonal opening.
- **Runtime components**: attach, set the relative transform, then register; a static component cannot be moved once registered in play, and a world transform set before attaching becomes the offset.
- **The test (`868 cave16`)**: walk every room along `FindPathWorld` steering 3 m ahead along the path (aiming at the next point cut bends into walls); rays from the tunnels' lines for holes; a capsule along each tunnel, blocked only if 1 and 2 m to either side are blocked too; `CaptureAbove16` (the set from 7 m over its floor, unlit) shows crossings and caps at a glance.
