# The list of 2026-11-16: the plan

The user's list is [improvements14.txt](improvements14.txt) (29 items). This plan breaks it into phases, each one PR (reviewed with `/code-review high`, its fixes tested again, merged when mergeable), in the order below. The user's choices (one question round, 2026-11-16):

- Potions and scrolls **move off the anvil**: potions only at the alchemist's table, scrolls only at the librarian's table; the anvil keeps repairs, food and the other things.
- **About half** of the wild containers are locked; anyone opens the unlocked ones; only the Rogue (picks) and the Warrior (breaks) open the locked ones.
- Villages 1 to 3 km apart **everywhere on land** (the arctic and the glaciers still have none).
- After the continent shrinks, an **old wilderness save loads in Brokenspire's square** of the new world (her hero, items, gold and quests kept; her place in the wilds and her map's discoveries dropped).

Stages go under `927` (`927_improvements14.py <part>`, as `914` and `926` did); C++ goes in new files `RD/RDList14*.cpp` where it is new, and in the existing files where it changes a rule. Each feature has a step in a level's scripted test (`884` Brokenspire, `888` the wilds, `868` the castle) with a name of its own, and its part of the level's document; what is not built or not measured goes in `TODO.md`. CLAUDE.md's stage list, the rules files (`wilderness.md`'s "300 x 300 km", `kethrys.md`'s placement) and `docs/tiers.md` are updated where a phase changes what they say.

## Readings of the list

Where the list's wording leaves a choice, this plan reads it so (the report says so again):

- **Item 3** says "the alchemist's table should be available in town..." in the librarian's item: read as the librarian's table (a typo).
- **Items 25 and 26** are one change: a place on the map (village, camp, lone house, ruins, cave, lair, ritual site, spawn point, structure, farmstead) is discovered within 500 m instead of 90 m. The small points of interest of the encounter director are not on the map and are unchanged. The map's fog (lifted 300 m round her) is not asked about and stays.
- **Item 22's "etc"**: minor roads lead to every place on the map that is not a city: villages, farmsteads, camps, lone houses, ruins, structures, caves, lairs, ritual sites.
- **Item 9's "wandering NPC"**: any person out in the wilds (road travellers, the director's travellers, farm folk, scenery and structure folk).
- **Item 11**: people in the wilds can be killed, except anyone giving or holding a quest she has not finished (they cannot die while it runs). Their piles hold mundane things (bread, cloth, a knife, a candle...) and a few gold.
- **Item 12**: the farm animals of the wilds (the farmsteads' pens and runs), not the towns'.
- **Item 13**: picking or breaking a lock alerts every person within 30 m, seen or not, and they turn hostile. **Item 14** adds: a person who sees it happen (a clear line within 40 m) turns hostile too.
- **Item 19**: lightning never strikes anyone under a roof; towns are not excepted.
- **Dungeon-only maps** (random_dungeonmagic_level5, martial_arts and the older levels) have no town and no wilds: with potions and scrolls moved off the anvil, those maps get the alchemist's and the librarian's tables in their dungeons, or they could make neither (item 3 names no dungeons; this keeps scrolls makeable there).

## The phases

| Phase | Items | What |
|---|---|---|
| 1 | 17, 18 | The tall spires without collision (save `game3b`); collision on every structure the generator builds |
| 2 | 1, 8, 20 | Sign lettering in its board; the last 20 messages; a potion or food on the quick bar used by the attack |
| 3 | 7, 10, 6 | The horse called from anywhere but a dungeon; the horse on the maps; the rider in the saddle's middle with the reins, her weapons put away |
| 4 | 5 | The Warrior's block: the shield's face toward the foe |
| 5 | 2, 3, 15 | The alchemist's and librarian's tables; ovens at the farms |
| 6 | 4 | Recipes found for advanced food, potions and scrolls |
| 7 | 16, 12 | Farm folk asleep at night; the farms' animals killed and looted |
| 8 | 9, 11 | People who can be hurt; monsters attack them; people killed and looted |
| 9 | 13, 14 | Locked wild containers, picked or broken; who hears and who sees |
| 10 | 19 | Storms by strength, lightning and thunder, lightning that hurts |
| 11 | 23 | The continent at 150 km, the cities' places scaled, the saves of the old world |
| 12 | 27, 28, 29 | Heaven on a volcano, Vel Morrath in the mountains, Kethrys Spire on a glacier |
| 13 | 23, 24, 25, 26 | 2.5 times the density and more along the roads; villages near roads, 1 to 3 km apart; discovery at 500 m |
| 14 | 21, 22 | Major cobbled roads to the cities, minor dirt roads to the places, signs with distances, the maps |
| 15 | | The Shipping package with the wild runs, and the final report |

Phase 1 comes first: the spires must be found in the world the user's save was made in, before any phase changes what the wilds lay. The world's phases (11 to 14) come last: they make a different world from the same seed, and every wild test's distances change with them.

## Phase 1: the spires and collision (items 17, 18)

- Load the user's save `game3b` (the packaged game's `%LOCALAPPDATA%\claude_ue5\Saved\SaveGames\save_game3b_f17369.sav`: seed 1588732281, her place on the farms 4 km from Brokenspire, decoded from its bytes) in the editor's play, find the tall structures round her and sweep her capsule into each. The first suspect is the tenth phase's landmark tower (its import's own convex shape, never walked into by a test); the far sights (the storm's funnel, the grass fire's 1.8 km plume) have no collision by design and drift 5 to 12 km off.
- If the editor shows them solid, repeat the sweep in the packaged game (the save is the package's): a cooked mesh can lose a shape the editor has.
- Every structure the generator lays (places, ruins, lairs, sites, scenery, farmsteads, houses, the landmark) is solid or is on a list of what is meant to be walked through (bushes, grass, effects, water skins, far sights, crops), and a test sweeps her capsule into a sample of every kind's solid pieces (`888 collide14`: none passes through).
- Fix what fails at its source (a mesh's collision in its stage, a component's settings where it is laid).

## Phase 2: signs, messages, the quick bar (items 1, 8, 20)

- **Signs (1)**: `bs_signs.py` paints only 9 of the 20 sign words (`RDTownPlan.cpp`'s `RDTSignText`); the 11 others (WARE/HOUSE, SLUICE/HOUSE, MONASTERY, WORKSHOP, LIBRARY, LABORA-/TORY, STUDY, MEDITA-/TION, TOWER, OFFICES, SHOP) fall back to a `UTextRenderComponent` of a fixed size with no fit. Picture the signs first to see which overflow (the user named the storehouse); paint every word, count the dark edge and the rule in the fit, and give the fallback a measured fit. Test: `884 signs14`: every sign's lettering inside its board, measured in pictures of each.
- **Messages (8)**: every line `SetMessage` gives (`ShowMessage` calls it) is kept with its game time, the last 20; a key and a pad button open a panel of them, newest first, on every map. Discovery lines and others given in one tick queue instead of replacing each other (the rules record lines lost so). Test: `868 log14`, `888 log14`.
- **The quick bar (20)**: food may go on the bar; with a potion or food chosen on the bar, the attack uses one, in every control layout (today only the Rogue's uses a readied slot by the attack). Test: `868 quick14` (a healing potion and a bread used by the attack, their counts down by one, her health up).
- Keys: from the free keys (J, K, L, N, O, U, X, Y, Z) and the pad's free buttons, checked against every panel; `docs/controls.md` updated.

## Phase 3: the horse (items 7, 10, 6)

- **Called (7)**: a key and a pad button call her horse wherever she is but a dungeon (the castle and the cities' dungeons refuse with a line); it comes from the nearest walkable spot within 40 m out of her sight. Test: `888 horsecall14` (in the wilds and in a town; refused in a dungeon).
- **On the maps (10)**: her horse, when she owns one, as a mark of its own on the minimap and the big map (the wilds' and the towns'). Test: `888 horsemap14` (the marks' places against the horse's).
- **The rider (6)**: her seat measured against the saddle's middle on each hero and moved forward to it; the reins: first check what the riding horse's mesh has (`ai models/ridinghorse.glb`: a bridle, reins, their bones or none); if it has none, reins of our own on its head bones; the rider clips' arms solved in Blender to hold them in the walk, canter and gallop; her weapons put away while she rides and drawn again when she gets down. Test: `888 rider14` (her pelvis against the saddle's middle, her hands against the reins, her hands empty, walking and galloping; pictures from the side).

## Phase 4: the Warrior's block (item 5)

- The block clip (`warrior3_block.py`, built on a boxing guard) keeps the guard's forearm turn, so the shield's face (the back of the forearm in the grip) points to her left. Solve the shield arm so the face points along her front; measure it in Blender (the face's normal within 20 degrees of her front) and in the game (`868 block14`: the face against her facing and the foe's way while blocking; pictures).

## Phase 5: the tables and the farms' ovens (items 2, 3, 15)

- Two new stations (`FRDRecipe::Station` "Alchemist" and "Librarian", as "Oven" and "Forge" are): the potion recipes move to the alchemist's table, the scroll recipes to the librarian's; the anvil keeps repairs, food and the rest; who brews and who reads a school stay as they are.
- Their pieces: an alchemist's table (a table, a cauldron or alembic, bottles) and a librarian's table (a desk, books, a candle, an inkwell), from the packs (Kethrys Spire's laboratory pieces), screened in pictures first.
- Where they stand:
  - **Towns**: the alchemist's table in the healer's house and the laboratories; the librarian's in the temple, the libraries and the studies; in every city that has those buildings.
  - **Dungeons**: an alchemist's table by each dungeon set's anvil (as `EnsureAnvil`: drawing no random number, so no layout moves), on every dungeon map; each map's start section built again (`build_start_section`) so the saved one has it. On the dungeon-only maps (see the readings) a librarian's table too.
  - **The wilderness**: both at villages (one village in two), the alchemist's table at some camps and structures (a hermit's hut, a shrine), the librarian's at ruins with books and the monasteries; an oven at every farmstead (in its house or yard), recognised as the towns' are.
- Level 5's crafting test (`853`) and the castle's (`868`) follow the move.
- Tests: `868 tables14` (the castle's alchemist's table brews a potion, the anvil offers none), `884 tables14` (both tables in Brokenspire, each making one), `888 tables14` (both in the wilds, a farmstead's oven bakes bread).

## Phase 6: recipes found (item 4)

- A recipe is an item of a new kind (as a tome: read, it teaches its recipe and is used up), kept in a saved list of recipes known; `RecipeRefusal` refuses an advanced recipe she does not know.
- New advanced recipes for food (meals that heal over time and give a short buff, from the gardens' and the hunt's ingredients), potions (greater healing and mana; speed, resistance, regeneration at the higher tiers) and scrolls (a spell at a higher rank, two spells in one), with their items, numbers and tiers in `SourceArt/balance/recipes14.json`, their pictures by the project's InvokeAI pipeline (`923 icons`), written to every map.
- Recipes are found in the dungeons' libraries and chests by tier, the wilds' ruins and structures' chests, and sold by the cities' traders.
- Test: `868 recipes14` (an advanced recipe refused, its recipe read, then offered and made at its table).

## Phase 7: the farms by night and their animals (items 16, 12)

- **Asleep (16)**: at night (the towns' hours) the farm family go into their farmhouse and sleep in its beds (`AS_Town_Sleep`, as the towns' do), and come out in the morning. Test: `888 sleep14` (at midnight each in a bed, the clip playing; at 8 at their work).
- **Animals (12)**: the farmsteads' pen animals take hits and die (as the wild animals do: health, a flinch, a death), and drop crafting things and food by kind (meat, hide, feathers, eggs, wool), kept dead in the save (a range of `WildKilled` of their own). Test: `888 farmanimals14` (a pig killed, its meat and hide taken; laid again, it stays dead).

## Phase 8: people who can be hurt (items 9, 11)

- Wild people get health and a way to be hit (her blows and bolts, monsters' blows), to flee, and to die (bodies stay; deaths kept in the save in a `WildKilled` range of their own); a quest's giver or holder cannot die while the quest runs.
- **Monsters attack them (9)**: a monster that meets a person before her takes the person as its foe (`ARDMonster::PickFoe`'s candidates, as the fighting guards are), strikes and can kill; a person flees, or fights back by role (as the town guards do: their fight reused without the town's tile paths).
- **Killed and looted (11)**: a killed person leaves a pile of mundane things and a few gold (tables by role).
- Test: `888 npc14` (a monster set on a traveller kills him; she kills a farmhand and takes his pile; a quest giver with a running quest is not killed).

## Phase 9: locks, who hears and who sees (items 13, 14)

- About half of the wild containers are locked (by a hash of their key: always the same); the prompt says so. The Rogue picks (a short hold); the Warrior breaks (a blow); the other heroes are refused with a line.
- **Heard (13)**: picking or breaking alerts every person within 30 m, and they turn hostile. **Seen (14)**: a person with a clear line to her within 40 m who sees it turns hostile too. Hostile people attack her (phase 8's fight) or flee by role.
- Test: `888 locks14` (the Rogue picks, the Warrior breaks, the Mage is refused; a farmer behind a wall 20 m off turns; one watching from 35 m turns; one 60 m off behind a wall does not).

## Phase 10: storms by strength and lightning (item 19)

- A strength drawn with each weather (light, moderate, strong, violent: rain, wind and cloud by it), by region in the game's own pick; a storm is moderate or stronger.
- Lightning in moderate storms and stronger, more often the stronger: a flash (the sky light and a bolt of our own mesh and material, as the far storm is) and thunder after it by its distance (343 m/s), the sound chosen from the library by name and measurement (`I:\game assets`: the project has no thunder; if the library has none, the report says so) and checked by a recording.
- A strike can hit anyone in the open (never under a roof): her through `HurtByTrap`, monsters, animals and people through their own damage; stronger storms strike harder and more often.
- Test: `888 storm14` (strengths drawn by region; strikes counted per minute at each strength; a strike on her hurts her, one on a monster hurts it; a recording of the thunder's delay).

## Phase 11: the continent at 150 km (item 23)

- The extent from 300 x 300 km to 150 x 150 km (`RDWild.h`), Brokenspire still at the south's middle; the climate, the continent's shape, the regions (`CellM`), the rivers, lakes and tracks, the far land, the map's zoom and tiles scaled to it; every biome still somewhere.
- The cities placed by the same rules at half the distances (their order along the road chain kept), so the tiers' legs halve; the quests' distances that assumed the old spacing.
- **A world version in the save**, raised by each world phase (11 to 14), each of which changes ids. A save of an older version made in the wilds loads in Brokenspire's square: her hero, items, gold, the towns' state and the town quests kept; her place in the wilds, her found places, her map's fog and her wild kills dropped; the wild quests (the captain's, the structures') given back to their givers to take again (their places move).
- The ids' bit budgets checked for the new grids (the rules record two collisions), with a test reading ids in the far north.
- The world's ground measured offline before and after (`RDWildProbe`, `wild_seams.py`), Graymourne's coast lift again.
- Tests: `888 world` (the extent, every biome somewhere, the cities' places, the road count), `888 save14` (an old-version save loads in Brokenspire's square, its wild quests back with their givers), and the other steps' distances.

## Phase 12: the cities' biomes (items 27, 28, 29)

- Heaven's region forced to volcanoes, Vel Morrath's to mountains, Kethrys Spire's to glacial (as Ashenreach's burned plain), the cone or the peaks beside the city, not under it; the city's ground levelled and its edge a slope, not a cliff (measured offline); no lava on a city or its road; snow and ice round Kethrys Spire.
- Test: `888 cities14` (each city's ground level, no lava within its square, its biome round it, no seam at its edge, pictures).

## Phase 13: density, villages, discovery (items 23, 24, 25, 26)

- 2.5 times the density of what the wilds place (places, points of interest, structures, scenery, farmsteads), by smaller cells, and more again within 1 km of the roads between the cities.
- Villages: the road refusal taken off; villages 1 to 3 km apart on all land but the arctic and the glaciers (a grid of their own, the other places' weights kept).
- Discovery within 500 m (see the readings).
- The encounter director sends nothing while anything is near her: with more near, its rule is measured and changed so encounters still come about every 40 s.
- Memory and frame rate of a walk measured before and after (the packaged walk was within 100 MB of its limit).
- Tests: `888 density14` (counts per kind against before; villages' nearest neighbour 1 to 3 km; villages by roads), `888 discover14` (a village found at 500 m), the director's gaps, the walk's memory.

## Phase 14: major and minor roads, signs (items 21, 22)

- **Major roads** (city to city): raised cobblestone, wider, their own look (a cobble layer in the ground and a kerb; the packs have cobble textures), in both `Sample` and `Height`; on the maps a look of their own.
- **Minor roads** (dirt): from the major roads to every place on the map but the cities (see the readings); the tracks give way to them. What reads the roads follows: `MakeCrossroads`, the scenery at crossroads, the travellers' roads, the tiers (`TierAt`) and the roadside rules.
- **Signs**: at regular intervals (every 2 km on a major road, every 1 km on a minor one, and at every fork), a post naming where the road leads and how far (painted names, distances in figures), facing the road.
- The ground's vertex encoding (`RDWildGroundVertex`, shared with the far land) and the shader's cost measured.
- Tests: `888 roads14` (every city's road cobbled and raised; every place reached; signs at their intervals naming the next city and its distance within 5 %; the maps' two looks; pictures).

## Phase 15: the package and the report

- The Shipping package with the wild runs (`package_mistward.ps1 -Out builds\list14 -Test`), then the final report: what was built, measured, not built, and the readings above.

## Working

- **One editor**: the C++ build, the stages and the play tests run one at a time; play tests in batches of five in a fresh editor (the machine is at its memory limit at play's start).
- **In parallel**: what is made outside the editor (Blender's signs, the block and rider clips, the tables, the reins, the cobbles, the lightning bolt; the InvokeAI pictures; the data files) can be made by subagents while a phase's tests run, each checked before its phase uses it.
- **Saves**: phase 1 uses `game3b` as it is; the world version keeps the user's saves loadable after phases 11 to 14.
