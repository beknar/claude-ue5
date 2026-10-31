# Converting Mistward Castle to Godot: feasibility

Written 2026-10-28. Mistward Castle can be ported to Godot, but it would be a rewrite of the game code plus a rebuild of most of the content's materials and effects, not a conversion. Before any of that, each Fab pack's license has to allow use outside Unreal.

## 1. The game code: rewrite it, but the design carries over

- The castle's logic is about 17,600 lines of dense Unreal C++ in the `RD` module (`claude_ue5/Source/claude_ue5/RD`; 25,500 lines in the whole module). The biggest files are the HUD (`RDHUD.cpp`), the room builder (`RDSection.cpp`), combat (`RDCombat.cpp`) and the generator (`RDDungeonGenerator.cpp`).
- Every line calls Unreal APIs: actors and components, instanced meshes, montages, Niagara, the Canvas HUD, Slate input. None of it compiles in Godot. It would be rewritten in GDScript or C#.
- The design ports well, because it is mostly the project's own logic: the section and room generator, tile paths, hash-based rolls, and the item, trap, slash and room tables as data.
- Most parts map to a Godot equivalent:

  | Unreal | Godot |
  |---|---|
  | Instanced meshes | MultiMesh |
  | Character movement | CharacterBody3D |
  | Animation montages | AnimationTree |
  | Canvas HUD | Control nodes |
  | Niagara effects | GPUParticles3D |

## 2. The content: the hard and slow part

- The castle's look comes from Fab packs: the castle, keep and dwarven pieces, the furniture kit, the monster gallery, the 27 armour sets, Stylized Slashes, Loot Drops and the spell effects.
- **Meshes and animations** can be exported from Unreal as glTF, which Godot imports, but they must be exported pack by pack. The armour fits and retargeted clips need checking after export.
- **Materials don't transfer**, so every one would be rebuilt as a Godot material or shader. They are Unreal material graphs with Substrate on, plus the project's own wound, outline and loot-pile materials.
- **Niagara effects can't be exported at all.** The spells, slashes, fountains, fires and traps' magic would all be remade by hand as Godot particles. This is probably the largest single art job.
- The project's own models (the Tripo heroes in `ai models/`, including the MartialArtist models) carry no licensing issue.

## 3. Licensing: check this before anything else

- Whether each pack may be used in another engine is not settled here. Some Fab content may be licensed for any engine and some only for Unreal; which applies to which pack has not been checked.
- Every pack the castle uses needs its license checked first. A pack that cannot move would need replacing.

## 4. What Unreal gives that Godot doesn't

- There is no Nanite: the castle's meshes would need LODs (Godot can generate them on import).
- There is no Lumen: lighting would use Godot's global illumination or baked light, and the torch-lit look would need tuning.
- Performance with this many pieces and lights is unknown until measured.

## 5. The tooling: all rebuilt too

- The pipeline, about 94 scripts and 19,000 lines in the dungeon line (`pipeline/unreal/760`-`870`), drives the Unreal editor through `ue_exec.py`.
- The 22-step test (`868_mistward_test.py`) drives play through Slate.
- The reels use the Movie Render Queue, and packaging (`pipeline/package_mistward.ps1`) uses Unreal's cooker.
- Godot has counterparts for each: scripted headless runs, a test framework, Movie Maker mode for reels, and export templates. They would be built fresh. A Godot MCP server is already configured in the user's Claude settings, which would help.

## Recommendation

Don't start with a full port. Do two cheap steps first:

1. List every pack Mistward uses with its license terms, which settles whether a port is allowed.
2. If they are clear, build a Godot vertical slice: the generator building tier 1's rooms from a few exported pieces, one hero walking and fighting one monster, and the HUD basics. That would measure how the export, materials and performance actually go before committing to the rest.
