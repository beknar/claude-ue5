# random_dungeonmagic_level5: design

How the game that [spec.md](spec.md) specifies is built: the classes and what each owns, the data and the scripts that fill it, what happens each frame, how randomness and state are kept, how the interface is drawn, and how it is tested and filmed. Derived from the spec and the C++ module (`claude_ue5/Source/claude_ue5/RD`) on 2026-10-24 (branch `level5-spells-rings-monsters`, commit `cfe1998`). Requirement IDs (`LOOT-3`) refer to the spec.

## Contents

1. [Principles](#1-principles)
2. [System context](#2-system-context)
3. [Source files](#3-source-files)
4. [Runtime objects and ownership](#4-runtime-objects-and-ownership)
5. [Data model](#5-data-model)
6. [Start-up and the frame](#6-start-up-and-the-frame)
7. [The world: sections, tiers, seals](#7-the-world-sections-tiers-seals)
8. [Interaction and loot](#8-interaction-and-loot)
9. [The player's side](#9-the-players-side)
10. [Monsters, corpses and allies](#10-monsters-corpses-and-allies)
11. [Build pipeline](#11-build-pipeline)
12. [Interface](#12-interface)
13. [Sound and music](#13-sound-and-music)
14. [Randomness and persistence](#14-randomness-and-persistence)
15. [Flags and isolation from the other levels](#15-flags-and-isolation-from-the-other-levels)
16. [Tests and reels](#16-tests-and-reels)
17. [Traceability](#17-traceability)
18. [Design debts](#18-design-debts)

---

## 1. Principles

- **Content is data, behaviour is C++.** The C++ knows how a weapon, a spell kind, a monster, a room kind or an item kind behaves; which weapons, spells, monsters, items, sounds and pictures exist is data on the level's generator, written by numbered pipeline scripts from JSON tables in `SourceArt/`. A table edit plus its script changes the game without a C++ build.
- **One actor owns the game.** `ARDDungeonGenerator` holds the tables, the world's state, the policies (loot, tiers, sound, volumes, heroes) and the input that is not combat. Other classes are workers it creates or finds.
- **The world is a pure function of seeds.** A section's plan and furnishing, a container's loot and a monster's place come from hashes and streams of the session seed, so a section can be dropped and rebuilt, and a reel repeats. What she *did* is kept separately, keyed by section and index, and laid over the rebuilt section.
- **Level 5 is a superset behind flags.** Six dungeon levels share the code; each feature level 5 added is switched on by data that is empty or a flag that is off elsewhere (§15).
- **Measured by tests.** Each class exposes counters and probes, and the test drives the game through the player controller's real input path (§16).

## 2. System context

```
SourceArt/*.json  ──►  pipeline/unreal/8xx_*.py  ──►  random_dungeonmagic_level5.umap
 (user's tables,        (run in the editor over         (ARDDungeonGenerator with its tables,
  measured frames)       ue_exec.py remote execution)     the saved start section)
                                                               │  play
Blender (tripo_build.py, weapon5_clips.py,                     ▼
 summoner3_armour.py) ──► FBX clips, refitted armour ──►  C++ module RD (runtime)
InvokeAI FLUX (rdm4_ui_gen/cut.py) ──► UI pictures ──────►  ARDHUD / FRDUIDraw
                                                               │
random_dungeonmagic_level5_select.umap  ──?Hero=Name──►  dungeon (ARDHeroGameMode)
                                                               │
853 test (828 driver) ──► test_<tag>.json        815 pilot + 816 MRQ ──► frames ──► overlay + assemble ──► reel
```

The editor is both the build tool (the scripts make and save assets and the level) and the test host (play-in-editor). A packaged game is not built for this level.

## 3. Source files

All under `claude_ue5/Source/claude_ue5/RD/`; the module also holds the town (`RT`), village (`IV`) and fighter (`SS`). Dependencies (`claude_ue5.Build.cs`): Core, CoreUObject, Engine, InputCore, ProceduralMeshComponent, Niagara, EnhancedInput, RenderCore, AudioMixer, SlateCore (runtime fonts), Slate (the editor key binding), HairStrandsCore (grooms on the MetaHuman face).

| File | Holds |
|---|---|
| `RDTypes.h` | every data struct and enum: pieces, monster kinds, sound sets, weapons, spells, items, armour fits, weapon fits, recipes, breakdowns, heroes, section progress, map data, UI art and fonts |
| `RDDungeonGenerator.h/.cpp` | `ARDDungeonGenerator`: the tables, sections and queue, seeds, map data and discovery, tiers and seals policy, loot policy, heroes, allies and corpses, sound, music, volumes, the Escape menu, the map's input, fall reset, the sound self test |
| `RDSection.h/.cpp` | `ARDSection`: one 252 m section: plan, shell, furnishing, lights, doors and containers, monsters, fire points, anvils, seals, map data, tile paths |
| `RDMonster.h/.cpp` | `ARDMonster`: a monster, a corpse or an ally: wandering, noticing, chasing, attacking, flinching, dying, freezing; wounds; voice; the spells' holds; ally behaviour |
| `RDCombat.h/.cpp` | `URDCombatComponent` (part 1): input, weapons and holsters, attacks, melee, bolts, being hit, death, inventory, items, armour, repairs, crafting, breakdown, the roll |
| `RDSpells.cpp` | `URDCombatComponent` (part 2): learning, the 22 spell kinds' release, lasting areas and auras, monster abilities on her, rings, buff lines |
| `RDBlood.h/.cpp` | `URDBloodComponent`: drops, sprays, splats, pools |
| `RDFace.h/.cpp` | `URDFaceComponent`, `FRDMetaFace`, `URDMetaFaceAnimInstance`, `ARDFacePuppet`: the face system (inactive on this level, spec FACE-1) |
| `RDHUD.h/.cpp` | `ARDHUD`: every panel, the maps, the menu's drawing |
| `RDUIArt.h/.cpp` | `FRDUIDraw`: nine-slice, fitted pictures, bars, text in a role with a runtime font cache |
| `RDHeroSelect.h/.cpp` | `ARDHeroSelect`, `ARDHeroSelectHUD`, `ARDHeroSelectGameMode` (the menu level), `ARDHeroGameMode` (the dungeon's pawn by hero) |

`RDHUD.cpp` (122 KB), `RDSection.cpp` (93 KB) and `RDCombat.cpp` (86 KB) are the largest.

## 4. Runtime objects and ownership

```
World (dungeon)
 ├─ BP_RDM4_GameMode : ARDHeroGameMode ── asks the generator for the chosen hero's pawn class
 ├─ ARDDungeonGenerator  (one; ticks while paused)
 │    ├─ Sections: TMap<FIntPoint, ARDSection*>      (start section saved; runtime ones spawned)
 │    │     └─ ARDSection
 │    │          ├─ instanced meshes, lights, Niagara fires, prefab actors   (static build)
 │    │          ├─ Doors[], Containers[] (FMover: pivot, parts, partner)    (interactive part)
 │    │          ├─ SpawnedMonsters[]: ARDMonster (living and corpses)
 │    │          └─ seal pieces and blocker boxes
 │    ├─ Allies[]: ARDMonster with bAlly (in no section's list)
 │    ├─ URDBloodComponent (made at BeginPlay with bCombat and a drop mesh)
 │    ├─ audio: attenuation cache, fire voice components, 4 music layer components
 │    └─ RevealPost post-process component, reveal curtains
 ├─ player pawn (the hero's Blueprint)
 │    ├─ URDCombatComponent "RDCombat"  (added by the generator in play)
 │    │     └─ weapon / off-hand / holster / loaded-bolt meshes, worn armour meshes (leader-posed),
 │    │        spell effects and lights, bolts in flight
 │    └─ (URDFaceComponent only when FaceChannels is set)
 └─ ARDHUD  (finds the generator; draws from its state and the combat component)

World (menu level)
 ├─ ARDHeroSelectGameMode (no pawn) ── ARDHeroSelectHUD (the card; mouse hit boxes)
 └─ ARDHeroSelect (turntable, figures, input, UIArt/UIFonts and Heroes copied from the dungeon)
```

Responsibilities in one line each:
- **Generator**: owns data and policy; creates sections, the combat component, blood, allies; plays every sound; answers questions (`GetMonsters`, `TierOf`, `LootListOf`, `ArmourRefusal`, `HeroLearns`, `MakeSpellWeapon`).
- **Section**: builds and owns one area and what stands in it; knows its tiles for paths; animates its doors and containers.
- **Monster**: one creature's behaviour; reports kills to the generator; hits her through her component.
- **Combat component**: everything about the hero: input, fighting, spells, her state, her bag, her gear.
- **HUD**: reads state, draws; hands the Escape menu's on-screen boxes back to the generator for the mouse.

## 5. Data model

### 5.1 Tables on the generator

| Property | Type | Script | Source |
|---|---|---|---|
| `Pieces`, `Effects` | `TMap<FName, FRDPiece>`, `TMap<FName, UNiagaraSystem*>` | `770` | the dungeon kit (inherited through the Save As chain) |
| `Heroes`, `DefaultHero`, `MenuLevel` | `TArray<FRDHeroDef>`, `FName`, `FString` | `825`, `852`, `856`, `858` | `heroes.json`, `summoner_hero.json` |
| `Items`, `StartRoomItems`, `MaxItemsPerContainer`, `ContainerLootChance` | `TArray<FRDItemDef>` ... | `825`, `855`, `857`, `858` | `items.json`, `weapons_table.json`, `armour.json`, `loot_table.json` |
| `Weapons` | `TArray<FRDWeaponDef>` | the hero's at `ApplyHero`; found and learned weapons appended in play | |
| `Spells` | `TArray<FRDSpellDef>` | `858` | `spells.json` |
| `Recipes`, `Breakdowns`, `bAnvilEverySection` | `TArray<FRDRecipe>`, `TArray<FRDBreakdown>` | `857`, `858` | `loot_table.json` |
| `Monsters`, `TierHealth` ... `TierAbility` | `TArray<FRDMonsterDef>`, `TArray<float>` | `859` | `monster_tiers.json` (+ measurements) |
| `MaxTier`, `SealPiece`, `EndPiece` | | `855` | |
| `bKeepCorpses`, `bEscapeMenu`, `KnightMonster`, `KnightStrength` | | `858` | `spells.json` `knight` |
| `Sounds`, `SoundVolume`, `MusicVolume` | `TMap<FName, FRDSoundSet>` | `797`, `825`, `857` | `sounds.json` |
| `UIArt`, `UIFonts` | `TMap<FName, FRDUIArt>`, `TMap<FName, FRDUIFont>` | `830 --level 5` | `ui_art/layout.json`, `fonts/` |
| Blood, `WoundMaterial` | | `798` (inherited) | |
| `bCombat`, `bStylizedMap`, `MonsterCoverage` | | `791` (inherited) | |
| `bTacticalMaps`, `bCasterControls` | | `821`, `825` | |
| `FaceChannels`, `FaceCues`, `FaceMeta` | | `834`, `840` (not on this level) | `face.json`, `face_mh.json` |

Two rules from experience shape the scripts: a `TMap` or struct read from one level's actor points into that actor, so data is copied between levels as text (`export_text` / `import_text`), never by reference (a reference hung the editor; `RollDodge` is a likely victim, §18); and a re-run of an earlier script rewrites its whole table, so later scripts that add to a table (`825` after `797`) must run again after it.

### 5.2 Key structs

- `FRDHeroDef`: name, title, pawn class, weapons, hit points, mana, mana a second, melee / ranged bonus, Rogue controls, roll clips, controls lines (keys and pad), card text (abilities, armour, starts with), accent, `Wears` (armour weights), `Learns` (spell types), `RingKinds`.
- `FRDWeaponDef`: one wieldable thing. Mesh, hand bone and grip, off-hand mesh; damage, reach, arc; attack clips with start, end and hit times, play rate; flinch and death clips; the spell part (`bSpell`, `bAlongside`, bone, bolt speed and turn rate, splash, charge / bolt / burst effects, light); the crossbow part (bolt mesh, muzzle, loaded bolt, stick time); holster bones; mana cost, icon, sound key; level 5's durability, ratings, type, `Item` (none = the hero's own), `SpellIndex` (the spell table entry; named so because `bSpell` is `spell` in Python), cooldown.
- `FRDSpellDef`: name, number, type, kind, the table's effect text, mana, cooldown, duration, drop chance, tier, damage, reach, radius, splash, amount, count, slow, burn, drain, pierce, bolt speed, five effect slots with scales, area repeat, colours, light, sound key, icon.
- `FRDItemDef`: name, kind (`Healing`, `Mana`, `Speed`, `Food`, `Armour`, `Weapon`, `Component`, `Repair`, `Ring`, `Tome`), amount, seconds, weight (rarity), tiers, found max, icon; armour fields (type, weight class, ratings, durability, slower, looks, `Fits`: hero → meshes); weapon fields (type, `WeaponFits`: hero → weapon def); ring kind; the tome's spell.
- `FRDMonsterDef`: mesh, parts, weapon mesh; idle, walk, attack, flinch, death clips and hit times; walk speed and the clip's own speed; capsule; mesh offset; health and damage factors; reach; attack interval; sound set; step length; tier, ability, title.
- `FRDSectionProgress`: rooms, rooms explored, chests (keys), chests looted, monsters planned, `Killed` (spawn indices), `Corpses` (spawn index → transform), `Consumed`, `bCleared`.
- `FRDSectionMap`: rooms and hallways (tile rectangles with `bCorridor`, `bDiscovered`), door, container and torch points, generated time, start flag.

## 6. Start-up and the frame

### 6.1 `ARDDungeonGenerator::BeginPlay`, in order

1. Session seed (`FixedSessionSeed`, else the clock); the reveal material's six slots; `SoundR` seeded with 90417.
2. With `bEscapeMenu`, the four volumes loaded from `GameUserSettings.ini`; spatialisation off under `-deterministicaudio`; attenuation cache cleared; the sound self test armed by `-RDSoundTest=`.
3. The blood component (with `bCombat` and a drop mesh); music stopped.
4. **The menu redirect** (FLOW-2): heroes, a `MenuLevel`, `rd.HeroMenu` ≠ 0 and no `?Hero=` → `bOpeningMenu`, open the menu, return.
5. `ApplyHero(ChosenHero())` before anything reads the player fields (HERO-2).
6. In the editor, ask every spell's Niagara systems to compile (they compiled on first use and showed nothing for seconds).
7. Map data reset; the start section generated if none is saved, else each saved section `ActivateForPlay`.

### 6.2 `ARDDungeonGenerator::Tick` (also while the game is paused)

1. Return while the menu level is opening.
2. `TickMenu`: Escape and the menu's keys and mouse. **Return if the menu is open.**
3. `PlayerCombat->TickInventory`: the inventory, repair and anvil panels' keys (this is how they work while paused).
4. **Return if paused.**
5. `TickAllies`.
6. With a player controller: add `URDCombatComponent` to the pawn if it has none (and the listener's attenuation point; the face component if there were face data); fall reset; set the audio listener; F / X → `InteractNearest`; M / Back → the map; the map's scroll input context and `MapPan`.
7. `TickMusic` (or the sound self test).
8. Around the tracked actor: queue sections ahead and near; drop far ones; `UpdateDiscovery`; every 0.2 s `UpdateFireLoops`.
9. Build: continue the section in progress for `FrameBudgetMs`, or start the next in the queue.

### 6.3 The pause model

The inventory, the anvil and the Escape menu pause the game with `SetGamePaused`. Game time stops: the combat component, monsters, sections and bolts do not tick, so cooldowns, effects and mana stand still. The generator alone ticks (`bTickEvenWhenPaused`) and works only the menu and the panels (steps 2-4 above). Consequences: tests that wait while a panel is open must wait on real time; a reel turns pausing off (`bInventoryPausesGame`, `bMenuPausesGame`) because Movie Render Queue renders a world that goes on.

## 7. The world: sections, tiers, seals

### 7.1 A section's life

```
Enqueue(S) ─(allowed by tiers, not built, not queued)─► Queue
   │ (one at a time)
   ▼
SpawnSection → BeginGenerate: GenR = FRandomStream(seed); Plan; ShellPrepare; AddDoors; RegisterMap
   │ each frame, FrameBudgetMs
   ▼
ContinueGenerate: shell columns → corners → Furnish(room) … → DecorateCorridor(hall) …
   ▼ finish
EnsureAnvil → flush instances → SpawnMonsters (own stream) → CollectFlicker → RegisterMap
   → RecordSection (Progress, first time only) → UpdateSeals
   │ she walks away (> UnloadSectionDistance)
   ▼
Destroyed (its monsters and prefab actors with it; MapData, Progress, LootedContainers stay)
```

- **Budget independence.** Every random draw of the plan and furnishing comes from `GenR` in a fixed order, whatever the frame boundaries, so a section built in one frame (`SetFrameBudget(1e6)` for reels) and over twenty frames are the same.
- **The start section** is built in the editor (`BuildStartSection`) and saved as static geometry. `ActivateForPlay` plans it again from `StartSeed` with the static build switched off and makes only the interactive part. Anvils are recorded by `AddPiece` before the static-build check, so a saved section's anvils are known in play.
- **`GenerateSectionNow`** finishes the section in progress before building another (starting a new one while another was half built abandoned it for good: a tier stuck at 15 of 16).
- **Plan.** Room kinds by weighted pick under caps, sizes within the block covering its centre lane, a Kruskal spanning tree over the 7 × 7 block grid plus 30 % of the other edges, hallways on the centre lines, portals at blocks 1, 3, 5 of each edge. Tiles: `Type` (void, room, hallway), `Owner` (room index or 1000 + hallway), `Blocked`, door edges. Paths are a BFS over walkable tiles that crosses owners only at doorways and junctions.
- **Furnishing** is code per room kind (`Furnish`, `DecorateCorridor`, `LightRoom`) placing pieces by name from `Pieces`; a missing piece is skipped. Every container goes through `AddContainer` (body plus a moving part on a hinge pivot). Wall variants use a position hash, not the stream, so adding variants does not move the layout.

### 7.2 What she did, kept by key

| State | Key | Kept in | Used on rebuild by |
|---|---|---|---|
| looted container | (section x, y, container key: a wardrobe's lower index) | generator `LootedContainers` | `ToggleContainer` (no loot), the maps' stars |
| discovered room | the map rectangle | `MapData` (copied into the new entry by `RegisterMap`) | maps, tier progress |
| killed monster | (section, spawn index) | `Progress[S].Killed`, `Corpses[index]` | `SpawnMonsters`: draw its randoms, then lay a corpse or skip |
| corpse used | (section, spawn index) | `Progress[S].Consumed` | never laid again |
| tier progress | section | `Progress[S]` | `IsTierOpen`, seals, the tier panel |

All of it is in memory only and emptied by `RestartPlay`.

### 7.3 Tiers and seals

- `TierOf(S) = max(|x|, |y|) + 1`; `IsTierOpen(T)` = T is 1, or T−1 is open and every section of T−1 has `bCleared`; `IsSectionAllowed` gates `Enqueue`.
- `RecordSection` fills a section's `Progress` the first time it is generated (rooms that are not corridors, chest and trunk keys, monsters planned). `UpdateProgress` runs on a discovery, a loot and a kill, sets `bCleared`, writes the notice, and when a tier opens calls `RefreshSeals`, which rebuilds every finished section's seals.
- `ARDSection::UpdateSeals` asks `GetSealKind` for each portal: 0 open, 1 shut tier (end wall inside the border, two half gratings, blocker), 2 past `MaxTier` (end wall, blocker). Visible pieces have no collision; an invisible `UBoxComponent` blocks bodies, so the wall can sit inside the border without a gap.
- `DebugClearSection` (tests, reels) discovers, loots and kills in one call.

## 8. Interaction and loot

```
F / X ─► InteractNearest
           ├─ anvil in her room within AnvilReach, nearer than any door/container ─► combat.SetCraftingOpen(true)
           └─ ARDSection::ToggleDoor / ToggleContainer (nearest within 260, containers +20 cm)
                 └─ container's first opening ─► MarkContainerLooted ─► UpdateProgress
                                                └► OnContainerOpened
                                                     └─ LootListOf(S, index) ─► for each pick: LootCountIn ─► combat.AddItem
```

`LootListOf` is a pure function (LOOT-7):
1. no loot unless `bStartLoot`, items, and the start section or `bLootAllSections`;
2. the great hall's containers take `StartRoomItems` in turn (guaranteed);
3. `ContainerHoldsLoot`: hash(SessionSeed ^ 0x51A7, section, index) against `ContainerLootChance`;
4. a stream seeded by hash(SessionSeed, section, index) picks 1 to `MaxItemsPerContainer` items by weight among those of the section's tier;
5. a generic tome becomes a tome of the tier's spells by drop chance (hash salt 0x70E3);
6. `LootCountIn`: 1 + hash(salt 0x2C3D) mod `FoundMax`.

Nothing here draws from a stream the play uses, so the opening order is free and reels repeat. `AddItem` then routes by kind (LOOT-10).

## 9. The player's side

### 9.1 `URDCombatComponent::TickComponent` (not while paused)

`PendingBreak` (weapons that reached 0, highest index first) → `TickSounds` (steps, the body falling) → `TickBolts` → `TickSpells` → dead? (revive after `RespawnSeconds`) → `TickDevice` → `TickCasterInput` → the roll's timer → the attack's timer (whoosh, release at the hit time, end) → mana regeneration → `TickEffects` (potions, food).

### 9.2 The weapons list

The generator's `Weapons` is the live list she wields from: her hero's at `ApplyHero`, then found weapons (`TakeWeapon`, one def per fit) and learned spells (`MakeSpellWeapon`) appended. The component keeps arrays parallel to it (`Wear`, `NextOf`) and maps keyed by weapon name (`ReadyAt` cooldowns). Removing a weapon (breaking, breaking down) removes it from all of them and shifts the indices; that is why breaking waits for the next tick (a bolt of it may still be flying) and goes from the highest index down. Holster components are made once at `Init` for the hero's own weapons only.

### 9.3 An attack

```
key ─► StartAttackWith(i): refusals (dead, busy, rolling, panel open, no clips) → mana → cooldown
        → clip = Attacks[NextOf[i]++ mod n]; target pick and turn; charge effect on the hand bone
        → PlaySlotAnimationAsDynamicMontage(clip, "DefaultSlot") ; mana and ReadyAt taken ; speed × 0.12
at AttackHit ─► melee: Strike()          (every monster in reach and arc → ARDMonster::ApplyDamage)
             ├► bolt kind / no spell: LaunchBolt()  → TickBolts: home, sweep vs capsules + trace walls
             │                                         → Burst / SpellBurst / SpellPierce / chain
             └► other spell kinds: ReleaseSpell()    → at once, or an Area / Aura / Drain for TickSpells
at AttackLen ─► EndAttack()
```

Damage is `GetDamageOf(i)` = damage × (1 + bonus) × (1 − weakness) at the moment of release (CMB-7); the monster multiplies by its curse. Wear (`WearOut`) is once per swing or burst that hit.

### 9.4 Spells

The table's kind selects a branch of `ReleaseSpell` (the 22 kinds of `ERDSpellKind`; 13, `Rend`, is unused by the table). Lasting effects are three kinds of state worked by `TickSpells`:
- **Auras** on her (ward with its hits or pool, skin, veil, mirror, pact, dispel immunity), one per kind, each with an effect attached to her root, ended with `DeactivateImmediate` + destroy (a plain deactivate left the mirror's hexagons on her: the packs' `User.Duration` is 999 s).
- **Areas** (cloud, pillar, rift, meteors, rune, sanctum): a place, a radius, damage a second ticked every 0.5 s, a slow, an effect re-fired every `AreaEvery`, meteor strikes as falling bolts.
- **The drain channel**: a target, ticks every 0.25 s, a wisp bolt every 0.3 s.

Holds on monsters (slow, curse, burn, knock, pull) are methods of `ARDMonster`. Spells draw only from `SpellR` (hash of the session seed, 0x5E11). Effects are spawned at component scale 1 with `User.Scale`, colours and `User.Duration` set before activation (Niagara sprite sizes here ignore component scale).

### 9.5 A blow on her

`ApplyDamage(amount, monster)` is a pipeline of checks in a fixed order (spec CMB-10): dodge window → sanctum → veil → ward → mirror → rune → armour + skin (≤ 95 %) → armour wear → hit points → pact → feedback (blood, sounds, hit number, flinch). Poison and the nova's price use `LoseHealth`, which skips the defensive steps. After the blow the monster calls `ApplyMonsterAbility`, which renews poison, weakness or slowness unless Dispel's immunity holds.

### 9.6 Bag and gear

- `Carried` (name → count) with `CarriedOrder`, `ArmourWear` (set → durability), `WornArmour`, `WornRings` (kind → ring), `Effects` (potions and food).
- Wearing armour makes one transient `USkeletalMeshComponent` per fitted mesh on her body mesh with `SetLeaderPoseComponent(body)`: the fits were made in Blender on her skeleton in her rest pose, so they follow her animation with no retargeting. `ArmourRefusal` on the generator holds the rules (weight, fit, the Mage).
- `UpdateMaxima` recomputes hit points and mana from the rings; `UpdateWalkSpeed` multiplies the character's saved speed by attack, potion, armour and slowness factors.
- Crafting: `PlanCraft` draws all parts from one running count (the kinds she has most of first), then `Craft` removes them; `BreakdownOf(type, tier)` gives materials × tier.
- The panels' content is produced as text lines (§12.2), so the HUD and the test read the same thing.

### 9.7 Input

The combat component reads keys with `WasInputKeyJustPressed` / `IsInputKeyDown` on her player controller (not Enhanced Input actions), which lets tests press them through `SimulateKey` and reach the same code. Run mode is the character Blueprint's `RunMode` variable, set by reflection; the Blueprint's `MoveScale` (`819`) reads it. The generator reads F, M, the map scroll and Escape; while the big map is open it adds `IMC_RD_MapScroll` at priority 1000 so the arrows do not also move her through the project's `IMC_Default`.

## 10. Monsters, corpses and allies

### 10.1 Spawning

`ARDSection::SpawnMonsters` with stream `RM = FRandomStream(seed ^ 0x5f3759df)`: shuffle the rooms, take round(n × `MonsterCoverage`) that have a free tile 15 m from the start room's centre; for each, draw tile, kind (`MonsterKindsFor`: the section's tier), yaw and the monster's own seed, **also for a killed one**, then spawn it, lay its corpse, or skip it. The spawn index is its place in this order. `Setup` sets the kind's mesh, parts, weapon, clips, capsule, and its hit points and damage from the tier tables, its speed, interval and ability strength from the tier factors.

### 10.2 Behaviour

No AI controller: `CharacterMovement` runs without one, and the monster steers itself in `Tick`. Its state is a handful of fields rather than a formal machine:

```
Wandering (WaitTime, Path) ──notice──► Aggro/Chasing (bAggro, replan 0.35 s)
     ▲                                     │ gap ≤ 0.7 reach, facing, cooldown 0
     └──lose (> LoseDistance)──────────────┤
                                           ▼
                                  Attacking (AttackTime, bHitDone) ─► cooldown
any ─blow─► Stunned (Stun) ;  any ─0 hp─► Dead ─0.8 s─► body down ─► Corpse (frozen) | sinks (other levels)
corpse ─Raise Dead─► Ally (bAlly, AllyLeft) ;  Knight spell ─► Ally + bChampion
```

Doors: a monster asks `IsTargetOpen` (where the door is heading), never its progress: at high tick rates a progress check toggled a door for ever. Paths are the section's tile BFS, straightened by probes.

### 10.3 Corpses and allies

- A kill reports to `OnMonsterKilled` (kill count, `Progress.Killed`, corpse transform, `UpdateProgress`). With `bKeepCorpses` the body freezes (animation paused, tick off, `OnlyTickPoseWhenRendered`): corpses cost nothing and stay.
- `RaiseAlly` / `SummonAlly` take a body out of its section's list into the generator's `Allies` and mark it consumed. Because her blows iterate `GetMonsters()` (the sections' lists) allies are never hit by her and never shown as monsters on the map. `BecomeAlly` makes it overlap pawns and ignore the camera channel; the ally hides itself when the camera is inside it. `TickAllies` keeps each ally's `Section` pointer on the section it stands in, so it walks that section's tile grid.

### 10.4 Wounds and blood

A wound is stored in the monster mesh's reference pose (the nearest skinned vertex to the strike, found on the CPU) and drawn by an overlay material instance per monster comparing with the pre-skinned position, so the pack's materials stay untouched and the wound stays on the skin in any pose. Blood is one component with two fixed instance pools (360 drops, 28 sprays) and decals with a cap; its stream is its own.

## 11. Build pipeline

Level 5 is a Save As copy of level 4, which descends from the combat level (`790`-`799`) and the base dungeon (`770`-`775`). The order that builds the current level (the [rebuild notes](levels/random_dungeonmagic_level5.md#rebuild) 11-14 have the commands):

| Step | Scripts | Makes |
|---|---|---|
| Level 4 base | `824` heroes' Blueprints and game mode; `825` Save As + heroes, items, sounds; `826` menu level; `830` painted UI; `831` menu first | the game level 5 starts from |
| The Summoner | `summoner3_prep.py`, `tripo_build.py` + `summoner3_clips.py`, `600`, `610`, `615`, `620` | `BP_JRPGSummoner3Character`, her clips |
| Armour | `849` export, `summoner3_armour.py` refit per hero, `851` import | `SK_S3_<set>`, `SK_<mesh>_<set>` |
| The level | move the old `.umap` aside, Save As level 4 → level 5, restart; `852`; `819`; `826 5`; `830 --level 5` | the Summoner as fifth hero, default hero, menu level |
| Weapons and tiers | `854` measure handles and static copies; `tripo_build.py` + `weapon5_clips.py`; `855` | 29 weapon items with fits, `MaxTier` 5 |
| Armour by weight | `849 heroes`, refits, `851 <mesh>`, `856` | `Wears`, fits, card text |
| Loot and crafting | `849 sets`, refits, `851`, `857`, icons, `830 --level 5` | 27 sets, loot table, recipes, anvils, fire volumes |
| Spells, rings, monsters | `build_cpp.ps1` (editor closed), `855`, `858`, `859`, pictures, `830 --level 5` | spells, rings, tomes, breakdown, corpses, Escape menu, 55 monsters |
| Docs | `rdm5_tables_doc.py` | the generated tables of `docs/levels/random_dungeonmagic_level5.md` |

Rules the order depends on: `819` after any script that recreates a caster Blueprint; `825` after `797`; `830` with absolute paths (it runs in the editor's working directory); after a C++ change build with the editor closed and relaunch; after a Blueprint compile from Python fetch class defaults again.

## 12. Interface

### 12.1 Composition

`ARDHUD::DrawHUD` draws in a fixed order (spec §19): the big map first (so every panel stays on top of it), the combat panels, the weapon bar, the minimap and tier panel, banners and prompts, notices, the inventory or anvil panel, the Escape menu last. Every size is a 1080p pixel count times `ClipY / 1080`.

### 12.2 The line protocol

Panels are fed by text lines with `|`-separated fields produced by the game side and parsed by the HUD: `GetInventoryLines` (`weapon|name[|left|full]`, `item|name|n`, `repair|`, `armour|name|worn|left|full`, `ring|`, `tome|`, `component|`, `carried|`), `GetRepairLines`, `GetCraftLines` (`recipe|item|can|label:have:need;...`, `breakdown|name|w<i>|drawn|item:n;...`), `GetBuffLines` (`label|seconds|good`), `GetMenuLines` (`volume|label|v`, `button|label`). The test reads the same lines, so what is drawn and what is checked cannot drift apart. The one flow the other way is the Escape menu's row and track boxes, which the HUD writes to the generator each frame for the mouse.

### 12.3 `FRDUIDraw`

A plain struct shared by the dungeon HUD and the menu HUD, pointed each frame at a `UIArt` and `UIFonts` map:
- `Nine` draws a piece nine-sliced (its border shares × its texture size × a pixel scale, shrunk if both borders exceed 98 % of the box); `Fit` draws one whole, centred, optionally mirrored; `InnerBox` finds a frame's open inside through the same stretch; `Bar` draws a dark backing, a fill picture cropped to the fraction, and the frame over it.
- Every call returns false when its piece is missing: each panel then draws its plain box, which is how the other dungeon levels (no `UIArt`) keep the old look with the same code.
- Text has three roles (title Cinzel, text Alegreya, label Alegreya SC). For a role with a face, a runtime `UFont` is made per role and point size (cache key role × 1000 + points, a `UPROPERTY` map so it is not collected) and drawn at the size shown, not scaled up from small glyphs; `Lift` raises each face so its capitals sit where Roboto's did, since every layout was made for Roboto's line. Labels are written as small capitals ("MANA BACK" → "Mana Back" in the SC face).
- The reels' overlay (`rdm4_ui_draw.py`, `rdm_reel_overlay.py`) re-implements the same rules and sizes in Pillow, because Movie Render Queue draws no HUD; a change to one must be made to the other.

### 12.4 Maps

A tile cache (`TMap<FIntPoint, uint8>`: generated, discovered, hallway bits) is built from all sections' map rectangles and rebuilt only when a hash of them changes. Points of interest are gathered each frame (monsters and elites within 25 m, unlooted chests and trunks in discovered tiles, unexplored exits, sealed ends, anvils seen). The minimap and the painted big map draw the same data at different scales; the big map snaps tiles to whole pixels and draws walls where a discovered floor tile meets no tile. World → screen: x = world Y, y = −world X.

### 12.5 Art and lettering pipeline

`ui_art.json` holds the prompts and styles; `rdm4_ui_gen.py` queues them on the user's InvokeAI server (FLUX), `rdm4_ui_cut.py` cuts each picture from its ground, measures borders and insides and exports PNGs with `layout.json` (`--merge` adds a batch to an export); `830` imports them as textures (`T_RDM4_*`, no mips, never streamed) and writes `UIArt`, `UIFonts` and the items' icons. Fonts are static TTFs fetched by `rdm4_fonts.py` (the repository's variable fonts draw only their default weight).

### 12.6 The menu level

`ARDHeroSelect` holds a copy of the dungeon's heroes, its own `UIArt` / `UIFonts`, the figures and the turntable; it reads the keys and opens the dungeon with `?Hero=`. `ARDHeroSelectHUD` lays the card out twice (measure, then draw on a board sized to it) and registers hit boxes for the mouse. `bStayOnConfirm` lets a reel render START without leaving.

## 13. Sound and music

- **One player.** Everything goes through `ARDDungeonGenerator::PlaySoundAt(key, where, volume, pitch)`: the set by key, a file from `SoundR` (never the same twice running), volume × `SoundVolume` × the player's volume for the key's category, pitch with variation; flat for 2D sets, else at the place with an attenuation object made once per (inner radius, falloff) pair (natural falloff, −40 dB at the end, low-pass with distance, spatialised unless `-deterministicaudio`).
- **The listener** is set by the generator every tick from the player controller, with her pawn as the attenuation point (a play-in-editor window without focus otherwise kept a stale listener; an unfocused window is also muted unless the test lifts it).
- **Fires** are recorded as points when their effects are placed (`TorchFire`, `HearthFire`, `BrazierFire` or anything scaled above 2); every 0.2 s the nearest within range get one of 6 looping voices, kept while they stay among the nearest, faded out in 0.3 s when dropped.
- **Music** is four flat components; the generator keeps each layer's position itself (a faded-out component restarts from 0) and switches the pairs on fight state (spec SND-5).
- **Volumes**: four floats, category by key prefix, applied to the layers and fire voices at once and to one-shots at their start, saved to `GameUserSettings.ini` on every change.

## 14. Randomness and persistence

| Stream | Seed | Draws |
|---|---|---|
| section plan and furnishing `GenR` | the section seed (StartSeed or session seed + coordinates) | room kinds and sizes, graph, furniture, lights |
| section monsters `RM` | section seed ^ 0x5f3759df | rooms, tiles, kinds, yaw, each monster's seed (also for the killed) |
| monster play `R` | its seed | waits, trips, attack clip choice |
| monster sound and blood `SR` | its seed ^ 0x2545f491 | voice and drip timers, wound jitter, wound material seed |
| light flicker | section seed + 99 | phases |
| loot | hashes of (session seed with salts 0x51A7, 0x70E3, 0x2C3D, section, index) and a per-container stream | what each container holds |
| generator sound `SoundR` | 90417 (re-seeded by `RestartPlay`) | which file of a set, fire offsets |
| music | session seed | which tracks |
| blood | 73113 (re-seeded by `Clear`) | drops, sprays, splats |
| her spells `SpellR` | hash(session seed, 0x5E11) | veil misses, area effect spots, meteors |
| face blinks | hash(session seed, 0x6A11) | blink gaps |
| summoned Knight | hash(session seed, 0x4B11) | its own `R` / `SR` |

The rule (NFR-1): nothing cosmetic draws from a stream that decides play, and nothing decided by order (which container first, how many frames a build took) feeds a stream.

**Persistence.** No SaveGame. Saved with the level by the editor: the tables and the start section's static build. Written by play: the four volumes and the editor's stop-play key binding. Everything of a run lives in memory and survives section unloading; `RestartPlay` clears it.

## 15. Flags and isolation from the other levels

| Gate | Level 5 | Switches on |
|---|---|---|
| `bCombat` | on | the combat component, fighting monsters, blood, wounds, exact monster coverage, music |
| `Heroes` non-empty (+ `MenuLevel`, `rd.HeroMenu`) | 5 heroes | `ApplyHero`, the menu redirect, inventory ticking, the wheel for every hero |
| `MaxTier > 0` | 5 | tiers, progress, seals, tier monsters and factors, the tier panel and labels |
| `Spells` non-empty | 30 | tomes, learning, the weapon bar, effect pre-compiling |
| `Recipes` non-empty, `bAnvilEverySection` | 5, on | anvils in every section, the anvil panel, map anvils |
| `bLootAllSections`, `MaxItemsPerContainer`, `ContainerLootChance`, `StartRoomItems` | on, 6, 0.33, 5 sets | loot everywhere, several items, the chance, the great hall's guarantee |
| `bKeepCorpses` | on | corpses that stay and are laid again |
| `bEscapeMenu` | on | the menu and the saved volumes (else all 1) |
| `UIArt` / `UIFonts` | 124 / 3 | the painted interface and lettering |
| `bTacticalMaps`, `bCasterControls`, `bRogueControls` | on, on, per hero | the maps, the casters' layout, the Rogue's keys |
| `FaceChannels` | empty | the face component |

Each check is local (`if (Gen->MaxTier > 0)`), so the combat level and magic levels 1 to 4, where these are off or empty, run the same code paths they always did; their tests (`793`, `813`, `828`) guard that.

## 16. Tests and reels

### 16.1 The test harness

- `828_rdm4.ps1 "<plan>" <tag> [maxSeconds] -lv 5` opens the level the plan needs (the menu level for `select`), sets `rd.HeroMenu 0`, starts play-in-editor, runs `853_rdm5_test.py` (a generator-style tick test kept alive with `__keep__ = True`), waits for `RDM5TEST done | <tag>` in the log, stops play and sets `rd.HeroMenu 1` again.
- Each step is a Python generator that yields frames; it presses keys with `SimulateKey` / `SimulateAxis`, reads counters and probes (`GetInventoryLines`, `GetBuffLines`, `MeasureArmourFollow`, `GetArtDrawn`, `GetMiniTierLabels` ...), records the output device for sound steps (`StartRecordingOutput`), takes `HighResShot` pictures, and writes `test_<tag>.json` (a record replaces the one before it).
- Helpers: `restart()` (`RestartPlay` with a fixed seed, the Summoner); `quiet()` (aggro 0 while measuring hit points or speed); `DebugClearSection`, `GenerateSectionNow`, `ReloadSection`, `SetSessionSeed` + `LootListOf` to find a seed with the wanted loot.
- The 23 steps and what each covers are in the spec ([§26.2](spec.md#262-the-test)).

### 16.2 Reels

Movie Render Queue renders the level itself: `814` makes a sequence with no tracks; `815_rdm_reel_pilot.py` is armed just before `816` starts the render and plays the game through the same calls (ways: armour, `weapons`, `heroes`, `craft`, `spells`, `grip`), turning pausing off, building sections in one frame, recording every row and event to `cine_<name>.json`; `829` pilots the menu level. `rdm_reel_overlay.py` draws the HUD, captions and keys over the frames from that record (the render draws no HUD), `rdm4_reel_assemble.py` cuts menu and runs together with the music, and `encode_video.py` writes the full and 20 MB files.

## 17. Traceability

| Spec | Design | Main code | Test step |
|---|---|---|---|
| §2 FLOW | 6.1, 12.6 | `BeginPlay`, `ChosenHero`, `ARDHeroGameMode`, `ARDHeroSelect` | `select`, 827 `menufirst` |
| §3 HERO | 5.2, 6.1 | `ApplyHero`, `FRDHeroDef` | `select`, `weapons`, `heroarmour` |
| §4 CTL | 9.7 | `TickCasterInput`, `TickInventory`, `TickMenu`, `TickDevice` | every step (keys pressed) |
| §5-6 WLD, GEN | 7.1 | `ARDSection::Plan`, `ContinueGenerate`, `ActivateForPlay`, generator `Tick` | `tiers`, `corpses` |
| §7 DOOR, CONT | 8 | `InteractNearest`, `ToggleDoor`, `ToggleContainer` | `loot`, `craft` |
| §8 LOOT | 8 | `LootListOf`, `ContainerHoldsLoot`, `TomeSpellOf`, `LootCountIn`, `AddItem` | `loot`, `chance`, `tierloot` |
| §9 TIER | 7.3 | `TierOf`, `IsTierOpen`, `RecordSection`, `UpdateProgress`, `UpdateSeals` | `tiers`, `maps` |
| §10 MON | 10.1-10.2 | `SpawnMonsters`, `MonsterKindsFor`, `ARDMonster::Setup` / `Tick` / `TickCombat` | `monsters`, `abilities`, `corpses` |
| §11 CMB | 9.3, 9.5 | `StartAttackWith`, `Strike`, `LaunchBolt`, `TickBolts`, `ApplyDamage`, `StartRoll` | `damage`, `weapons`, `spells` |
| §12 WPN | 9.2 | `TakeWeapon`, `WearOut`, `BreakWeapon`, `855` | `weapons`, `breakdown` |
| §13 SPL | 9.4 | `LearnSpell`, `MakeSpellWeapon`, `ReleaseSpell`, `SpellBurst`, `TickSpells` | `spells`, `abilities` |
| §14 RING | 9.6 | `WearRing`, `UpdateMaxima` | `rings` |
| §15 ARM | 9.6 | `WearArmour`, `ArmourRefusal`, `WearDownArmour`, `MeasureArmourFollow` | `wear`, `heroarmour`, `follow`, `damage`, `armourtable` |
| §16 INV | 9.6, 12.2 | `SetInventoryOpen`, `UseInventoryEntry`, `UseItem`, `GetInventoryLines` | `ui`, `repair` |
| §17 REP, CRF, BRK | 9.6 | `BeginRepair`, `RepairEntry`, `SetCraftingOpen`, `PlanCraft`, `Craft`, `BreakDownWeapon` | `repair`, `craft`, `breakdown` |
| §18 ALY | 10.3 | `RaiseAlly`, `SummonAlly`, `BecomeAlly`, `FollowPlayer`, `TickAllies` | `spells`, `corpses` |
| §19-20 HUD, MAP | 12 | `ARDHUD`, `FRDUIDraw`, `DrawPaintedMap`, `GatherPois` | `ui`, `maps`, 827 `map`, `stars` |
| §21 MENU | 12.6 | `ARDHeroSelect`, `ARDHeroSelectHUD` | `select`, 827 `menuui` |
| §22 ESC | 13 | `TickMenu`, `SetUserVolume`, `ApplyUserVolumes` | `menu` |
| §23 SND | 13 | `PlaySoundAt`, `GetAttenuation`, `UpdateFireLoops`, `TickMusic` | `fire`, `menu`; `799` sound self test |
| §24 GORE, FACE | 10.4 | `URDBloodComponent`, `ARDMonster::AddWound`, `URDFaceComponent` | combat level `792`; face on the earlier levels (`812`) |
| §25 NFR | 14, 15 | streams, flags | reels repeat; other levels' tests |

## 18. Design debts

The spec's [§27](spec.md#27-known-deviations-and-open-issues) lists the behaviour that differs from what was meant. The design reasons behind several:

- **Copying data between levels by reference.** Structs and maps read from one level's actor and set on another after a map load are unsafe (an editor hang with a `TMap`; very likely the (1, 1) `RollDodge`). Copy as text, and have a test measure each copied value on the target level.
- **`ActivateForPlay` is not idempotent.** It rebuilds doors and containers after clearing them but appends monsters without clearing the old ones, so every `RestartPlay` adds a start section's worth. Clearing `SpawnedMonsters` (and their actors) there would fix it.
- **Data written on one line with a comment.** `859`'s capsule assignment hides behind a `#`. Its test checks hit points, speed and tier, not the capsule against the mesh.
- **The generator is large.** It owns world, loot, tiers, heroes, sound, music, volumes, the menu and the map's input (588-line header). Natural seams if it grows further: a sound/music service, a loot service, a tier service, each a plain struct or component the generator holds, as `FRDUIDraw` already is for drawing.
- **One HUD file for everything** (122 KB). The panels share only `FRDUIDraw` and the line protocol, so they could be split by panel without changing behaviour.
- **Behaviour duplicated in Python.** The reel overlay mirrors the HUD's rules; nothing checks that they agree except looking at frames.
- **Card text is data copied at build time.** The Summoner's card kept `852`'s wording because `856` rewrites only the other heroes; card text written from the tables (as the level document's are) would stay true.
