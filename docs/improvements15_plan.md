# The list of 2026-11-20: the plan

The user's list is [improvements15.txt](improvements15.txt) (30 items and the instructions in item 31). This plan breaks it into phases, each one PR: built, tested with a step of its own in a level's scripted test, reviewed (`/code-review high`), its fixes tested again, then merged, in the order below. After the last phase the Shipping package is built (a full cook) and run. An independent review of the first draft found 19 problems (a contradiction read silently, phases too large, risks to memory, save compatibility and the tier rules, tests that would not measure the thing itself); this version answers them.

The user's choices (one question round, 2026-11-20):

- **Item 20:** 'The First Warden' is offered from the start; taken after the Tier 1 boss is dead, the kill she already made counts and she can hand it in at once.
- **Item 23:** **every landmark tower** (the 182 m broken towers, one per 6 km square of open land) holds a cave entrance. One new procedural cave level serves them all, its tier set by where the entrance stands.
- **Item 25:** **all of [wilderness_ideas.md](wilderness_ideas.md) but climbing and gliding:** ideas 1 to 6 and 8, the open parts of 7, and 9 without climbing.
- **Item 31:** each PR is merged after its review, then the next begins.

Stages go under `934` (`934_improvements15.py <part>`, as `927` did for list 14); the cave level is `935` (its Save As and build, as `897` did for the sewers). C++ goes in new files `RD/RDList15*.cpp` where it is new, and in the existing files where it changes a rule. Each feature has a step in a level's scripted test (`868` the castle, `884` Brokenspire, `888` the wilds) with a name of its own and a stated measure, and its part of the level's document; what is not built or not measured goes in `TODO.md`. CLAUDE.md's stage list and order, and the rules files, are updated where a phase changes what they say. Every stage that runs "on every map" includes the new cave map from phase 9 on.

## Readings of the list

Where the wording leaves a choice, the plan reads it so (the final report says so again):

- **Item 3:** an ally in her way steps aside: while she presses toward an ally within reach, it moves off her line, sideways, to a free spot.
- **Item 4:** read literally ("if there are no damaged minions or if there are maximum number of minions, the spell is refused"), she could never summon her first minion (none is damaged). The plan reads it as: below the cap, a cast adds a minion as now; at the cap, it replaces the most damaged of that spell's minions (lowest share of its hit points); at the cap with none damaged, it is refused before mana is taken, with a message.
- **Item 7:** the searched bookshelf's cabinet doors swing open and stay open (the Gothic pack has no door meshes: they are split off in Blender).
- **Item 12:** a blessed rune stone looks exactly like a cursed one (same mesh and material) and gives one of the existing buffs for 60 s with "The rune stone blesses you: ...". It is drawn on a random stream of its own, so the cursed stones and every seed's other traps stay where they are; the Rogue sees it as a rune stone (the same outline) and can disarm it as she can a cursed one.
- **Item 13 ("unwieldy" read as unwield):** the Summoner can put the dagger away: an "unarmed" weapon entry of her own (the Martial Artist's "Fists" pattern, a real entry, never an index of -1), chosen in the inventory like a weapon; spells and the quick bar work with it.
- **Item 14:** scrolls go on the quick bar for any hero who can read them.
- **Item 15:** claiming anything that is not a potion plays a thud from the sound library; potions keep the bottle sound.
- **Item 16:** the ankh lights the way and marks unlooted chests and trunks; it stops revealing traps and the other containers (the Rogue still sees traps).
- **Item 17:** "repaired via the repair items" needs something to repair: the torch and the ankh get a burn time (durability) that wears while held lit; at 0 they go out; the repair items restore them, as they do armour. Today neither wears.
- **Item 18:** the Summoner chooses among 5 kinds per tier for each summon spell (the current kind one of the five; four more from that tier's monster table, followers that fight, no bosses); the choice is kept in the save and carried with each minion.
- **Item 19:** the circle's town trip gets a pad button free while its prompt shows, in every control layout, and the prompts show the device's keys.
- **Item 20:** the boss goal counts only Mistward Castle's own tier-boss counters (`bossdone:<tier>` without a dungeon key), not Vel Morrath's, the other dungeons' or the caves'.
- **Item 21:** the town map's functional buildings show a symbol instead of their text label, in the painted and the satellite map, in every city plan (Brokenspire, holy, forge, port, mage, modern), and a legend panel explains the symbols, the seals and the spots.
- **Item 22:** every fireplace the game places that shows no fire (measured in pictures, in the editor and the package) gets a visible animated fire and a crackle.
- **Item 23:** each cave is **one tier**, the tier of the region its tower stands in ("of the same Tier that the region is coded for"): the level's tier rings all play that tier. The castle-only systems are off on the cave map: the keys chain, the final boss, the bosses' unique rewards (chi attacks, unlocked spells), the arena and the cells. A cave's boss gives the tier's loot and gold. Each tower's cave keeps its own state under its own key (the tower's cell). No key is needed to enter.
- **Item 26:** a village on sloping ground has its buildings and its square on level terraces cut into the hill, held up by stone retaining walls with buttresses; a village of 12 or more buildings gets a low wall or a watch platform on its top terrace ("fortifications"). Villages are placed on the ground as it is without terraces (so the terraces depend on the village, never the other way round).
- **Items 27, 28:** villages have 8 to 15 small buildings, each a household of 2 to 5 people living there (by day at work round the village, by night asleep in its beds), as the farm families do, and counted by the wild people rules. To keep the memory in bounds, people beyond 250 m of her are dormant (no tick, no animation), as the herds are.
- **Item 29:** every door of a village or farm building has steps that reach the ground (no 6-step cap; a landing when long), and a plinth under any modelled stair that ends above the ground.
- **Item 25:** see phases 10 to 17. Idea 9's road signs naming places and distances, and the roads drawn by kind, were built by list 14's fourteenth phase (PR #92); what is left of it is the waystones, the crossroads posts naming the towns down each road (the crossroads kinds have no such post yet), and the roads coloured by tier. Idea 4's "more carrying space" has nothing to act on (the game has no carrying limit): collectibles are traded for hit points, mana or a rank of a secondary ability.
- **Item 24:** the Ultimate Horse work of 2026-11-18/19 is committed in phase 1 and is in the final Shipping package (a full cook: it adds saved fields).

## The phases

| Phase | Items | What |
|---|---|---|
| 1 | 24, plan | The Ultimate Horse work committed; this plan |
| 2 | 2, 3, 9, 30 | The Summoner's allies: solid to her, stepping aside, back beside her in the arena, summoned in the wilds |
| 3 | 4, 18, 13, 14 | Summons: replacing a damaged minion, five kinds per tier; the dagger put away; scrolls on the quick bar |
| 4 | 5, 6, 7, 8, 11 | The dungeon: an oven in the start room, the stations' symbols on the maps, bookshelf doors, the big map's zoom, the chapel's pews |
| 5 | 10, 12, 15, 16, 17, 19 | Items: scroll icons, blessed rune stones, the equipment's thud, the ankh, the torch and ankh repaired, the circle's town trip on the pad |
| 6 | 1, 20, 21, 22 | The town: the cows kept apart, 'The First Warden', the town maps' symbols and legend, the fireplaces' fire |
| 7 | 26, 29 | Village ground: terraces and retaining walls; stairs to the ground (world version 6) |
| 8 | 27, 28 | Villages: 8 to 15 buildings, households living there |
| 9 | 23 | The cave complex under every landmark tower |
| 10 | 25 (1, 2) | Landmarks of each region, the night's smoke and windows; lookout towers that reveal the map |
| 11 | 25 (3, 9 in part) | Named roaming monsters; roads coloured by tier and the danger on the map |
| 12 | 25 (4) | Collectibles, treasure maps, named items |
| 13 | 25 (5) | Contracts on the towns' boards |
| 14 | 25 (6) | Cleared camps as waypoints; resettled ruins; the share reclaimed |
| 15 | 25 (8) | Story encounters on the road |
| 16 | 25 (9 in part) | Waystones; crossroads posts naming the towns |
| 17 | 25 (7) | Warm gear, hot meals, desert heat, cooking for resistance |
| 18 | | The Shipping package (full cook) and its runs; the final report |

**Order.** The horse first (finished work, and every later phase builds on that tree). The dungeon and item phases (2 to 5) are small and independent. The town (6) next. The world's phases after: the village ground (7) and villages (8) change what the wilds lay, so the caves (9) and the wild ideas (10 to 17) are built and tested in the world as it will stay. Phase 14's resettlement uses phase 8's households.

**The world's version.** Changing what the wilds lay drops the wild state of saves from an older world (their hero, items, gold and quests are kept; list 14's rule). The changes are grouped: phase 7 raises the version once (the terraces and the villages' new size and layout, both read from the ground model); phases 10 to 17 add places only where nothing stood (landmarks, lookouts, roaming rounds, waystones) on streams of their own, so the existing places stay put and no further version change is needed (each is checked: the world's places before and after compared for a fixed seed). The user's save `game3b` and its tower are looked at in phase 9 in the world of phase 7. Old saves' loss of wild progress is said in phase 7's PR and the final report.

## Parallel work

One editor runs on the project at a time (CLAUDE.md), and a C++ build needs it closed, so the phases are built one after another. Beside them:
- **Blender art** for later phases, while the editor is idle or closed (Blender and a playing editor together have run the machine past its commit limit twice): the bookshelf's split doors (4), the town maps' symbols (6), the retaining walls and buttresses (7), the cave kit's survey (9), the waystones and posts (16).
- **Data and text** (quest, contract and encounter tables, buff tables) drafted while the editor runs tests.
- **Reviews:** each PR's code review runs as an independent agent while the next phase's art is prepared.

## Phase 1: the horse, and this plan (item 24)

- Commit the Ultimate Horse work: `RD/RDHorse15.cpp`, `RDHorseAnim.*`, `RDReel15.cpp`, `RDReel16.cpp`, the changes to `RDHorse*`, `RDTypes.h`, `RDDungeonGenerator.*`, `RDCombat.cpp`, `RDHUD.*`, `RDList14b.cpp`, `RDMistward5.cpp`, `RDGameInstance.h`; `933_horse15.py`, `888`'s horse steps, `record_mistward_autoplay.ps1 -Reel15/-Reel16`, `blender_numpy/reel15_cut.py`; `SourceArt/brokenspire/horse15.json`, the test record `test_h15g.json`; the docs and rules; and this plan. Not committed: `ai models/frigate-test.glb`, `frigate-4b.glb`, `MartialArtist3-old.glb`, and `SourceArt/list10/warrior3_block/build.json` (a Blender build record of absolute paths, kept out by the standing rules).
- Build and run `888 horse15,horse9,horse14 -Light` on the tree as committed.

## Phase 2: the Summoner's allies (items 2, 3, 9, 30)

- **Solid to her (2):** `ARDMonster::BecomeAlly` (`RDMonster.cpp`) makes allies block her and her them, while they still pass each other and the monsters as now. Test `868 allies15`: she walks into an ally and stops at it (her capsule's distance to it never under the sum of the radii); three allies and two monsters crossing in a hallway do not jam (each reaches its goal within 5 s), with `bAllySpacing` on and off.
- **Stepping aside (3):** `AllySpacingPush` / `AllySteer` (`RDMistward4.cpp`) gain a yield: an ally within 1.2 m ahead of her while she presses toward it moves off her line to a free spot. Test: she walks a hallway through a line of three allies; each steps aside within 1 s; she reaches the far end (her path's length measured).
- **The arena (9):** `StartArena` (`RDMistward2.cpp`) brings every living ally into the arena room beside her when the doors shut. Test `868 arena15`: allies left behind a door are inside the room's rectangle when the first wave spawns.
- **In the wilds (30):** `SpawnMonsterKind` / `SummonAlly` fall back to the wilds' section (`EnsureWildSection`, open ground) where no dungeon section is; `FollowPlayer` follows on open ground (no tile path), brings allies back beside her when left behind (riding, fast travel, a town's gate), and `FindAllySpot` works on open ground; allies take no people or farm animals as foes (no witness or lock rule set off by them); carried-in allies are placed in the wilds too; the autoplay's and the reel's guards go. Test `888 summon15 -Light`: she summons in the wilds; the minion follows 100 m on foot and after a ride of 300 m, fights a wild monster to its death, and never targets a farm animal or a traveller beside it.

## Phase 3: summons and the Summoner's hands (items 4, 18, 13, 14)

- **Replacing (4):** the refusal in `StartAttackWith` (`RDCombat.cpp`) becomes the reading's rule. Test `868 summon15`: below the cap the cast adds one; at the cap with one hurt minion the cast replaces it (count unchanged, the replaced one gone, the new one at full health); at the cap with none hurt, refused, mana unchanged.
- **Five kinds per tier (18):** `FRDSpellDef::SummonKind` becomes a list of 5 (`934 summons` chooses them from the tier's monster tables, and checks every kind exists in the `Monsters` table of every map she plays: the castle, the dungeons, Brokenspire and the wilds); the chosen kind per spell is kept in the save, carried with each ally across levels (`RDCarry.cpp`), shown in the summons panel (`RDHUD.cpp`), and autoplay picks among them; the inventory's spell row and the pad cycle it. Test: each kind of each tier summoned on two maps, follows and fights; a carried minion keeps its kind through a level change.
- **The dagger put away (13):** an "unarmed" entry in the Summoner's weapons (no mesh, a label), chosen in the inventory like a weapon. Test: chosen, her hands hold no mesh (the weapon component's mesh none), she casts, she draws the dagger again.
- **Scrolls on the quick bar (14):** `IsQuickableItem` (`RDMistward2.cpp`) takes scrolls; the bar's use reads the scroll. Test `868 quick15`: a scroll on the Summoner's bar and on the Mage's, read by the bar, the count down by one, its spell cast.

## Phase 4: the dungeon (items 5, 6, 7, 8, 11)

- **The start room's oven (5):** `EnsureOven` beside `EnsureTables14` (`RDList14c.cpp`): a bread oven on a free tile off the lanes of the great hall, no random draw, recorded in `TownOvens`; `934 oven` builds the saved start sections again on every dungeon map. Test `868 oven15`: an oven in the great hall, usable (a bread baked), and the hall's anvil, tables and stairs still where they were (their places before and after compared).
- **Symbols (6):** `ARDHUD::GatherPois` (`RDHUD.cpp`) adds the ovens, the alchemist's table, the librarian's table and the forge as kinds of their own, drawn on the minimap, the big map and its legend like the anvil (`map_oven`, `map_alchemist`, `map_librarian`, `map_forge`). Test: each marked once discovered (the HUD's mark list read) and seen in a picture of the minimap.
- **Bookshelf doors (7):** the Gothic cabinet's doors split off in Blender as hinged parts (`blender_numpy/shelf_doors15.py`); the searched shelf opens them, kept with the shelf's state. Test: a searched shelf's doors turned open (their angles measured), an unsearched shelf's shut.
- **The big map's zoom (8):** zoom on keys free while the big map is open in every control layout (the wheel, + and -, and a pad pair checked against `bCasterControls`, `bRogueControls` and the Martial Artist's); `DrawPaintedMap` and `DrawTacticalMap` scale by `MapZoom` about the pointer or her mark. Test: zoom in and out; the map's scale measured (a room's width in pixels); her mark stays put.
- **The pews (11):** `Furnish`'s chapel case (`RDSection.cpp`) turns the pews to face the altar, the bench's front measured in its mesh. Test `868 chapel15`: every pew's front within 10 degrees of the way to the altar.

## Phase 5: items (items 10, 12, 15, 16, 17, 19)

- **Scroll icons (10):** each scroll's icon is its spell's (the weapon's `Icon`), in `934 scrolls` on every map, run after `910`, `918` and `928` (which adds the advanced scrolls). Test: every scroll's icon equals its spell's.
- **Blessed rune stones (12):** a trap kind `Blessed` with the cursed stone's mesh and material, drawn on a stream of its own (the cursed draw unchanged): a buff for 60 s and the message. Test `868 runes15`: each kind's effect and message; the two the same mesh and material; a fixed seed's cursed stones and other traps where they were before.
- **The thud (15):** a sound set `Player.Loot.Gear` (a thud or wooden knock from the library, converted by `rdc_sound_prep.py`, chosen by name and measured); claims choose it for anything not a potion. Test: claiming a sword and a potion with the output recorded (`StartRecordingOutput`, `bAllowBackgroundAudio`): each recording's first sound matches its set's file (`rdc_sound_check.py`).
- **The ankh (16):** `TickAnkh` (`RDList10c.cpp`) marks only unlooted chests and trunks. Test: within range, chests and trunks marked, traps, barrels and crates not.
- **Torch and ankh repaired (17):** a burn time on both (shown in the inventory), worn while held lit, dark at 0, restored by the repair items. Test `868 light15`: held 30 s they wear by 30 s; at 0 the light is off; a repair item restores the full time.
- **The circle's town trip on the pad (19):** a pad button free while the circle's prompt shows (checked against every layout), and the circle's and tier pads' prompts show the device's keys. Test: the pad's button takes her to Brokenspire.

## Phase 6: the town (items 1, 20, 21, 22)

- **The cows (1):** `ARDTownAnimal` (`RDTownLife.cpp`) keeps a pen's animals apart (a separation push, walk targets not taken, spawn spots apart); the wild pens use the same class. Test `884 cows15 -Light`: over 60 s no two animals of a pen closer than the sum of their half-widths, in the town and a farmstead.
- **'The First Warden' (20):** its `after` removed in `town.json` (offered from the start, `882`); the boss goal reads Mistward's own tier-boss counters. The same for `scholar_bones`. Test `884 warden15`: offered at the start; taken after a Tier 1 boss kill it reads 1 / 1 and is handed in; a Vel Morrath boss kill does not count.
- **The town maps (21):** symbols for the functional buildings in place of text, in both map modes and every city plan, and a legend panel; new symbol art where missing. Test: pictures of each city's map: each kind's symbol at its building and in the legend, no building text label left.
- **Fireplaces (22):** find every fireplace piece the game places and picture it in play and in the package; the ones without a visible fire get one (`NS_Fire` at a measured scale) and a crackle (`Fire.Hearth`). Test: a picture of each kind with its fire; the crackle in a recording near one.

## Phase 7: village ground (items 26, 29; world version 6)

- **Terraces (26):** where a village's ground slopes, its buildings and its square stand on level terraces: the ground model's height (`Height`, `Sample`, `BareHeight` and the shared ground vertex `RDWildGroundVertex`, so the walked, drawn and far land agree) is flattened on each terrace and blended at its edges; villages are placed on the ground without terraces. A retaining wall with buttresses stands along each terrace's low edge (pieces from `blender_numpy/terrace15.py`, imported by `934 terrace`, with collision). The villages' new size and layout (phase 8's 8 to 15 buildings) are laid here, in the same world version, as plain houses; phase 8 fills them.
- **Stairs (29):** `FitWildHouse` (`RDWild10.cpp`) and `WildKitBuilding` (`RDWildFarm11.cpp`): steps reach the ground at every door, and a plinth under modelled stairs that end in the air.
- Test `888 terrace15 -Light`: in 10 villages on slopes (Hawkby by name), each building's floor and the ground under its footprint within 15 cm, the retaining walls standing on their low side, and every door reached on foot (her capsule walked from the ground in through it); `RDWildProbe` and `wild_seams.py` over the villages' squares and the roads to them: no new seam; `888 stream` (the memory walk) unchanged within its bounds.

## Phase 8: villages lived in (items 27, 28)

- Each building a household of 2 to 5 (from the farm families' kinds and lines), living, working and sleeping there (`SpawnWildFarm11`'s spawner, `TickWildFarmDay`), talking, counted by the wild people rules; dormant beyond 250 m. Test `888 villages15 -Light`: in 10 villages, buildings 8 to 15, people 2 to 5 per building, by night in their beds; `888 stream` and the frame time with three villages loaded within their bounds.

## Phase 9: the caves (item 23)

- **The level:** `935 saveas` (a Save As copy of `mistward_castle`, as `897`), `935` builds its theme "Cave": rooms and hallways as caverns and tunnels (rock walls, uneven floors, stalactites, rock arches for doorways) from `Content/Cave`, the vaults (`RDCeilings`) as rock, dim light (`DungeonLightTint`), beasts and underground kin from the tier's table, the saved start section built again under the theme (no throne, carpet or banners). One tier per cave (the reading); the castle-only switches off. Its materials' usage flags (`869`), the package's map list (`package_mistward.ps1`) and a run hook for it.
- **The entrance:** a doorway in the landmark tower's base (a cave mouth where it has none), F to enter, the tier from `TierAt` at the tower carried in the travel; the way back to the tower's foot; each tower's cave its own state.
- **game3b:** the tower near the user's save, and what stood by it, looked at in play.
- Test `888 caves15 -Light` and `868 cave15 -lv caves`: entered from two towers of different tiers, each cave's monsters and loot of its region's tier, a picture of the first hall (no castle pieces), the way back to the tower.

## Phase 10: landmarks and lookouts (ideas 1, 2)

- **Regional landmarks (1):** one or two tall silhouettes per region of its own (a giant tree, a smoking crater, a broken spire, a beam of light by night), drawn far, placed on a stream of their own; camps show smoke and houses lit windows at night. Test `888 landmarks15 -Light`: from three hilltops per region, the landmarks within view counted (at least three), in pictures by day and night.
- **Lookouts (2):** the Old Watchtower and a lookout per region: reaching the top reveals the region's places on the map as unvisited marks. Test `888 lookout15 -Light`: climbed, the region's places' marks appear (counted), other regions' not.

## Phase 11: roaming monsters and the map's danger (ideas 3, 9 in part)

- **Named roaming monsters (3):** a few per region, named, on set rounds, well above the region's tier, some only by night or in storms; a unique named item once each, kept dead in the save, a mark on the map once seen. Test `888 roamers15 -Light`: a roamer found on its round, its tier above the region's, killed, its item given once, dead after a save and load; a night roamer absent by day.
- **The map's danger (9):** the roads coloured by tier, a skull near a roaming monster once seen. Test: in a picture of the map, each road's colour matches its tier.

## Phase 12: rewards that last (idea 4)

- Region collectibles (a kind per region) traded at a town for hit points, mana or a secondary ability's rank; treasure maps found loose in ruins, each a picture of a spot by a landmark (rendered in play), leading to a buried chest; unique named items tied to places (one per structure kind). Test `888 rewards15 -Light`: collectibles counted in the save and traded; a map's chest found where its picture shows; a named item in its place's chest once.

## Phase 13: contracts (idea 5)

- Named beasts posted on the towns' boards; tracks and signs on the trail teach a weakness that makes them take more damage. Test `888 contracts15 -Light`: a contract taken, the trail's signs read, the beast's damage taken measured with and without the weakness.

## Phase 14: cleared camps (idea 6)

- A bandit camp or lair, once cleared, becomes a friendly waypoint (a trader, a bed, a fast-travel point); after some game days people (a household of phase 8's) move into the nearest ruin; the map shows each region's share reclaimed. A game-time skip hook for the test. Test `888 reclaim15 -Light`: cleared, the trader and bed there; days skipped, the ruin lived in; the share on the map.

## Phase 15: story encounters (idea 8)

- A courier with a letter for her by name (from someone she has met), someone chased, a broken-down cart, a rival adventurer who reaches places first across the wilds (the director's kinds, `events11.json`). Test `888 stories15 -Light`: each sent by the director's hook and played to its end.

## Phase 16: getting about (idea 9 in part)

- Waystones she finds and lights, travelled to beside the towns; a post at each crossroads naming the towns down each road (the road signs' lettering). Test `888 waystones15 -Light`: a waystone lit and travelled to; a crossroads post's names match the towns its roads lead to.

## Phase 17: preparing for regions (idea 7)

- Warm gear (armour with warmth) and hot meals keep the cold off; the deserts' heat by day drains her without water or shade; cooking with the regions' herbs and game gives resistance buffs. Test `888 climate15 -Light`: her drain measured in the cold with and without warm gear and a hot meal, and in a desert by day and night.

## Phase 18: the Shipping package

- `package_mistward.ps1` with a full cook, every map including the caves; its runs: each map loads and plays; brokenspire's wild walk; the horse ridden; a cave entered from a tower; a village visited. The final report says what each phase built, what was measured, and what was not.
