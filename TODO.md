# TODO

[README](README.md) · [The wilderness](docs/levels/wilderness.md) · [Brokenspire](docs/levels/brokenspire.md) · [Vel Morrath](docs/levels/vel_morrath.md) · [Ashenreach](docs/levels/ashenreach.md) · [Graymourne](docs/levels/graymourne.md) · [Kethrys Spire](docs/levels/kethrys_spire.md) · [Heaven](docs/levels/heaven.md)

What is still to be tested and done, and the known limits. Written 2026-11-03 for the wilderness and the castle's final boss (the user's spec of 2026-11-03, [docs/wilderness.txt](docs/wilderness.txt)), merged that day in PR #16. Remove an item when a test shows it working or the work lands; add one when a limit is found.

## To test

Built and compiled, but no test has run it yet:

- [ ] **The hero menu's CONTINUE** (C or the pad's X): it loads the newest of the two saves. Test: a save written, the menu opened, CONTINUE, and she arrives where the save says.
- [ ] **The Escape menu's Load page loading a game:** the test checked the page's lines (which save, where, when; since the list of 2026-11-04 every named save among them); the load itself was tested through the code, not through the page's choice.
- [ ] **A load into another town:** she saved in Vel Morrath (or Ashenreach, or Graymourne), and the load builds that town first and puts her in it.
- [ ] **The autosaves on Quit and before the Mistgate** (`quit`, `castle`): the other autosaves (a place found, a town entered, before and after a journey) have run in the tests.
- [ ] **Coming back to life in the nearest found town** after a death in the wilds (`WildRespawnAt`): the nearest found town, not the nearest town, and it is loaded at once.
- [ ] **The teleport circle's journey to another town** (Brokenspire's circle to Vel Morrath's and back, and refused in a fight).
- [ ] **The maps switching in Ashenreach's and Graymourne's walls:** both are built round her and their people are their own in tests (`884 forge`, `port`), but no test has walked in through their gates, nor read the town's map there.
- [ ] **The caldera's steam and the volcanoes' lava** seen in a picture from her view (the code places them; no picture has shown them yet).
- [ ] **The packaged game in the wilderness:** the package of 2026-11-06 (`builds\vel_morrath`) runs the town, puts her out in Vel Morrath and builds the city round her; a walk out of the gate, a journey, a save and load, and its memory over a long walk have not been run in it (worker threads, transient map textures and the save all behave differently packaged).

## The list of 2026-11-12 ([docs/improvements12.txt](docs/improvements12.txt))

Done in phases (1 to 3 so far): 1 gold, the map in its scroll, the mouse on the big map, rd.MapTeleport, the saves as cards; 2 the horses' gaits; 3 the twenty ruins; to come: 4 the hidden lairs; 5 the structures and quests; 6 tiers 26-30; 7 the Rogue's abilities.

- [ ] **Phase 1, what is not measured:** ([Brokenspire](docs/levels/brokenspire.md)):
  - The mouse on a town's big map beyond the teleport's click (its drag and wheel were there before).
  - The teleports' outcomes are measured by calling the click at its screen point: through Slate the real mouse resting over the play window pulled the game's pointer to itself and turned presses into drags (`RDMAPPOINTER`'s log: the pointer jumped to the same spot every time). The pointer's own path (a pick under it, the wheel, a drag, a click that travels) is measured through Slate.
- [ ] **Phase 2, the horse's gaits, what is not done or measured:** ([Brokenspire](docs/levels/brokenspire.md#the-horses-gaits-the-list-of-2026-11-12-second-part)):
  - The horse walks only below 4 m/s: with the keyboard her walk is its canter, and its walk needs a light touch on the stick.
  - A gait change carries on at the same point of the stride, but the two gaits' poses are not blended: the legs still change shape in one frame.
  - The Blender horse (`SourceArt/brokenspire/horse/`) is built with the same gaits but not imported: the game rides the Tripo horse.
  - Nobody has watched the gaits in motion: they were judged in eight still frames a gait and two in-game pictures.
- [ ] **Phase 3, the twenty ruins, what is not done or measured:** ([the wilderness](docs/levels/wilderness.md#the-list-of-2026-11-12-third-part-twenty-kinds-of-ruins)):
  - The ruins are set pieces of the packs' meshes over the land: the catacombs, the barrow's passage and the rock-cut temple have no inside beyond their entrance; the tell is a mound, not dug into.
  - Two kinds are rare round Brokenspire (one submerged town and one sand-buried city within 150 km): their biomes and water are rare there.
  - Some pictures show little of their ruin: the tell's mound is low, the barrow and the catacombs' entrance are small at 45 m, and the sand-buried city's (in the canyons) is hidden by a canyon wall; the pieces' readouts say they stand there.
  - A piece's collision is its mesh's own: whether she can walk through every doorway and up every step was not tried.

## The list of 2026-11-11 ([docs/improvements11.txt](docs/improvements11.txt))

- [ ] **Phase 3 (spells, curses, slashes), what is not measured:** ([the castle](docs/levels/mistward_castle.md#the-list-of-2026-11-11s-third-part)):
  - Lethargy's slower blows (the monsters' wait between blows) and Brittle's knock-down beyond the doubled blow's stun.
  - Silence breaking a shot's wind-up, and the fear under a stun: the review's fixes, read in the code; no shooter or stun was put in the test.
  - The hunted mark seen through a wall on the map.
  - Withering Brand acts on heals only: no monster heals itself.
  - Elemental Ruin takes the element of her last spell (the list said "choose": there is no chooser).
  - The ten new slashes have no pictures (none of the twenty older ones has one either).
- [ ] **Phase 4 (the farmsteads), what is not done or measured:** ([the wilderness](docs/levels/wilderness.md#the-list-of-2026-11-11-fourth-part-the-farmsteads-designs)):
  - The farm buildings have one storey.
  - The gardens give their crops once a game (the town's grow again).
  - The farm folk still stand at their work.
  - Only the first farm's buildings were walked into; the 60 designs were measured as data (buildings, furniture, containers, gardens, animals), not walked.
  - The frame rate in a designed farm was not measured against the old layout.
  - Not in a packaged game yet: the kit's pieces are the town's, which `869` covers, but no Development package's log has been read for them.

## The list of 2026-11-10 ([docs/improvements10.txt](docs/improvements10.txt))

Done in phases, a PR each (the user's choices of 2026-11-10: the ankh lights, outlines traps and shows hidden things; the forge is the Warrior's; the liveliness ideas built, the best of them). The first, the quick fixes, is built and tested ([Brokenspire](docs/levels/brokenspire.md#the-list-of-2026-11-10-first-part): `868 list10,recipes,options,shields,gearbreak,slots,tabs`; `888 list10w,horse9 -Light`; `884 noshield9,start9,backspace9,services,list7 -Light`). Still to do:

- [ ] **Phase 1, what is not done or measured:** found weapons still break at 0 durability (the list's "like weapons": only shields were changed, to armour's half). The quick bar's drawing (the items' counts, the durability bars) is seen in pictures, not measured. A save made before 2026-11-08b keeps the start shield she carried then. The quest window shows the quests of every town on the castle's level (the giver's town is not named on it). The Save page's drop-down lists the newest eleven saves. The ambushers chase at their kind's own speed (a slow kind walks at 1.5 m/s: from 57 m it takes about half a minute). `884 list7` failed once on its pig (the pen's fence in every way first, `test_b10a.json`). Not packaged yet.
- [ ] **Phase 2, what is not done or measured:** built and tested ([Brokenspire](docs/levels/brokenspire.md#the-list-of-2026-11-10-second-part), [Mistward Castle](docs/levels/mistward_castle.md#the-list-of-2026-11-10s-second-part): `884 sky10,stair10,see10,castlewalls -Light`, `868 list10b,arena5`; PR #39's review fixed). The sky's border and disc are judged in pictures, not measured. The far land is coarse (its nearest ring 1.1 km out, 96 points round): a mountain's outline past 10 km is a soft shape. The town watchtowers' spiral stairs (Castle Forge's quarter turns) are as they were: the list named the castle's guard towers, whose stair this is. The see-through hides only the town's instanced pieces: the doors and their leaves, the trees and the wilds' own pieces (which the camera passes through) are not hidden; a hidden piece's shadow goes with it. The prisoners' mark is drawn for the sets built (a set dropped far off shows none, as its chests). The shelves' and the boss teleporter's states are the level's (a trip to the town and back finds the shelves full again, as the castle's chests outside the first set). The far land is made in one go on the game thread (about 12 ms every 150 m: on the horse every 8 s or so). Not packaged yet.
- [ ] **Phase 6, what is not done or measured:** built and tested ([the wilderness](docs/levels/wilderness.md#the-list-of-2026-11-10-sixth-part-houses-to-walk-into-the-farms-on-the-map-travellers), [Brokenspire](docs/levels/brokenspire.md#the-list-of-2026-11-10-sixth-part-the-towns-liveliness)). The houses have one room on the ground: the open houses have no upper floor and no stair inside, and the hermit's hut (laid at 0.6) keeps its doors shut. A wild house's chest is furniture, not a container (nothing to find in it). The barn has collision now but no inside. Only the Old Watchtower has a stair; the ruins have none. A hen's round is the tile it stands on (1.2 m round: it cannot stray into a stall), so it runs a metre at most. The travellers walk through what stands on the road (they keep to its points, nothing stops them) and camp only on roads. The picture from the tower's top shows its wall (the camera has no room in the ring). Other liveliness ideas not built are listed in the final report of the list.
- [ ] **Phase 5, what is not done or measured:** built and tested ([Brokenspire](docs/levels/brokenspire.md#the-list-of-2026-11-10-fifth-part): `884 animals10,farms9`, `888 horse9,life7`, all with `-Light`). No `cow.glb` was given: the cows are still the Blender ones (`tripo_animals.py` takes one when it comes: a `cow` kind and its file). One colouring a kind (the Blender ones had two or three; the cow's second is left out so the pens keep their shares). The skin is weighted by distance (no heat solve): the pictures show creases at the goat's belly in its walk and the pig's neck in its graze, and the rabbit's ear stretches in its flick; the chicken and rabbit walk slower than the Blender ones (22 and 19 cm/s against 35). The rider's clips were not changed: her seat measured 14.0 cm over the saddle bone, as before.
- [ ] **Phase 4, what is not done or measured:** built and tested ([Brokenspire](docs/levels/brokenspire.md#the-list-of-2026-11-10-fourth-part): `884 lines10,sleep10,people10 -Light`). Measured in Brokenspire only: the other towns of the wilds have the households and the beds too but were not walked at night (their frame rates with 25 % more people not measured). The drunk and the Dwarf smith have no Sleep clip (other skeletons) and sleep standing where they are; the tavern's customers sleep at their tables. A bed put for a sleeper goes on a free tile of its building (a keeper's in the smithy or the temple too). Nobody reads the lines but their counts: 1020 lines written by agents, checked by number and by role, not each by eye.
- [ ] **Phase 3, what is not done or measured:** built and tested ([Brokenspire](docs/levels/brokenspire.md#the-list-of-2026-11-10-third-part): `868 list10c_forge,list10c_oven,list10c_ankh,list10c_block,block`, `884 forge10 -Light`). The ankh drops only from a dungeon's tier-2 monsters (the wilds' monsters drop none: their tier is the roads' bands, not the sets' ring) and is found in its containers. The ankh's "what hides" has nothing to show (no monster is stealthed or invisible) and there are no hidden caches but the containers; the forge makes only the game's tier-1 arms and armour, and looting before 2026-11-10 counts nothing (the record began then). The forges are not on the map. The block's stance is the Warrior's own rig only (Warrior3: every map's); its sword hand lies 11 cm short of the hip's point. The full `list10c` was run in its four parts (one run is ten minutes; Claude Code stopped two whole runs for the machine's memory). Not packaged yet.
- [ ] **Phase 7, what is not done or measured:**
  - **Done:** the rebalance was tested in each city and dungeon ([docs/tiers.md](docs/tiers.md#the-tests): `868 tier25` on the five dungeons past the castle, `868 tiers` on the castle, `888 cities25,wild25 -Light`). What is used up (potions, food, scrolls, repair items, torches) now grows past tier 5 as a kill's gold does.
  - **Not done:**
    - The repair items are tiers 1 to 5 only (no copies in the later dungeons' loot), so past the castle they come only from the store.
    - Nobody has fought past tier 5 under autoplay (the balance there is by construction).
    - The town's prices are read from the store's lines, not bought from in a trial at tier 25.
    - The cities' tiers were set through the game instance, not reached by play.

## The list of 2026-11-08b ([docs/improvements9.txt](docs/improvements9.txt))

Done in phases, a PR each ([Brokenspire](docs/levels/brokenspire.md#the-list-of-2026-11-08b-first-part), [the wilderness](docs/levels/wilderness.md#the-list-of-2026-11-08b-first-part)). The first, the quick fixes, is built and tested (`884 storage9,start9,backspace9,time9,noshield9,sky9,crops9` with `-Light`; `868 startgear,shields,death,block`). The second, the medieval farms, is built and tested (`884 farms9,crops9` with `-Light`, the probe and `wild_seams.py`; [the wilderness](docs/levels/wilderness.md#the-list-of-2026-11-08b-second-part-the-medieval-farms)). Still to do:

- [ ] **The farms, what is not measured:** five of 29 croft yards in the probe's 5 km have no farmstead (on a slope or a road: their yard stays grass); the farmhouses and barns were whole meshes (not entered: since the list of 2026-11-11 every farm building is built with its inside and door); the farm folk do not walk, sleep or go in at night; the furrows between strips are drawn as soil but the 2 m ground grid softens them at a distance; the frame rate in a farmstead's chunk (29 props, 8 or 9 animals, 4 people) not compared with the fields'; the farmsteads' pieces in the packaged game (`869`: the Lake Village's and the castle kit's materials need the instanced-mesh usage? they are placed as single components, not instances) not checked.
- [ ] **Phase 3, the dungeons' keys, what is not done or measured:** built and tested (`884 keys9`, `868 finalboss`); the dungeons' tier bands came with phase 5 ([docs/tiers.md](docs/tiers.md)). Vel Morrath's, Ashenreach's and Graymourne's last tier's bosses dropping the next key is measured only through the same drop called in Brokenspire (`keys9`), not by killing them in their dungeons. The keys and maps have no pictures (the inventory shows their names). The packaged game with the keys (its runs that go down take `-RDAllKeys`) not packaged yet.
- [ ] **Phase 4, Kethrys Spire and Heaven** with their dungeons: Kethrys Spire and its tower's dungeon are built and tested ([its section](#kethrys-spire-and-its-tower-2026-11-08b-docslevelskethrys_spiremd)); Heaven and its fortress behind "Kratos Aurorim Research, LLC" are built and tested ([its section](#heaven-and-its-fortress-2026-11-09-docslevelsheavenmd)).
- [ ] **Phase 5, the rebalance to tier 25, what is not done or measured:** built and tested ([docs/tiers.md](docs/tiers.md): `868 tier25 -lv vel_morrath`, `888 wild25 -Light`). The dungeons' own bosses wait for the user (each dungeon's tier bosses are still the tier's strongest kind). The balance past tier 5 is by construction (the monsters' hit points grow as her power, their blows as her hit points: as many blows each way as at tier 5), not by trials: `868 balance` plays tiers 1 to 5 only, and no hero has fought at tiers 6 to 25 under autoplay. Only Vel Morrath was played (its tiers, loot, tomes, boss); the War Engine, the Sewers, Kethrys Spire and Heaven read the same tables. The later abilities borrow their source's look (Crashing Wave is Chain Punch's blast, stronger; Barbed Bolt the crossbow's bolt) and picture; the quality copies their base's mesh and picture. The town's prices past tier 5 (x 1.17 a tier) not seen in play. Not packaged yet.
- [ ] **Phase 6, the secondary abilities, what is not done or measured:** built and tested ([docs/secondary.md](docs/secondary.md): `868 secondary`, `888 secondary9 -Light`). The abilities have no pictures (the quick bar shows two letters) and no looks of their own but the swarm's lights and the steps' teleport flash (the shields, the stun, the push, the leap show nothing on her or the monsters). Tested at rank 1 (the ablation at 2): the higher ranks' numbers come from the same table. Her ranks carried between the town, the wilds and a dungeon and kept in a save go through the same carry as her learned spells, but no test has carried them. The Wall Run is a leap (it climbs a wall only to a floor on top of it, up to half its length higher); no picture of her on the water. The Rogue has none (the list names none). The balance of the abilities (their cooldowns of our own) not played under autoplay, which does not use them. Not packaged yet.
- [ ] **Phase 7, the points of interest every 40 s, what is not done or measured:** built and tested ([the wilderness](docs/levels/wilderness.md#the-list-of-2026-11-08b-seventh-part-something-every-40-seconds): `888 poi7 -Light`). The kinds are made of the wilds' existing pieces (a milestone is a standing stone, a hermit's hut a small house, a giant's bones a big skeleton): no signposts, bridges, ferries, ships, inns, towers or wagons of their own; the list's NPCs (travellers, merchants, pilgrims, quest-givers in the wilds, fights in progress, kidnappings, world events like a dragon's attack, puzzles, stables) are not made: the director's encounters are ambushers, a pack and a lost satchel. The points of interest are not on the map, have no pictures and no notice when seen. In the mountains and one pine forest the world's spacing leaves gaps of up to 7 min (the director fills them in play: measured only on the grasslands' run). Landmarks are seen only within the chunks' 1 km. `stream`'s memory read +1078 MB and then +119 MB (its earlier readings vary as much); not packaged yet.
- [ ] **Phase 8, the ridable horse, what is not done or measured:** built and tested ([Brokenspire](docs/levels/brokenspire.md#the-horse-the-list-of-2026-11-08b-eighth-part): `888 horse9 -Light`). Its gallop's stride is short (the legs reach 30 cm a half stride): at her ridden speed the clip plays near 3 times its rate. The rider clips are a camel rider's: she leans forward with her legs hanging, no stirrups; no mount or dismount clip (she is put on and off). Ridden, the horse has no collision of its own (her capsule moves; its body can pass into trees and walls); standing unridden it stops her since the list of 2026-11-10. Tested with the Warrior only; the other heroes' rider clips are made and set, not ridden in a test. The stable has no building (a spot by the gate with its horse); no horse in the dungeons; riding while she was mounted is not saved (she comes back on foot, her horse beside her). Not packaged yet.
- [ ] **The grey disc in the sky** ("still appears whenever there is any blue sky"): not seen in pictures straight up and at 60 degrees, clear and fair, at 9, 12 and 16 o'clock, with the high clouds' dome shown and hidden; where and when the user saw it is to be asked. The clouds' new mode (half-size tracing) may have taken it with the edges' fringe.
- [ ] **The clouds' new mode's cost:** the frame time of `r.VolumetricRenderTarget.Mode 1` against 0 not measured (two readings of one setting in the editor varied twice over).
- [ ] **The new crops in the packaged game and from afar:** not packaged yet (`869` first: the new crops' materials need the instanced-mesh usage); the peas read as a low mat in rows, the flax shows thin bundles at the rows' ends, and the hemp alone looks like a sapling (the Blender previews).
- [ ] **`888` with the thirteen crops:** `fields8` and `perf8` not run since (the crops' kinds and their plants' count changed).

## The list of 2026-11-07 ([docs/improvements8.txt](docs/improvements8.txt))

Built and tested (`884 planks`, `storage`, `block8` (`test_b8b`; `test_b8`'s block8 failed on the turn, 56 degrees of 60); `888 rain8`, `sky8`, `fields8`, `ground8`, `animals8`, `speed8`; `868 block`); still to test or do:

- [ ] **`884 dummies` to pass:** its only kept record, `test_b8`, failed: the Mage's bolt at the dummy counted 0 hits (the sword and the bolt at the target counted). Run it again.
- [ ] **`888 perf8` to run again:** its record was not kept, so the farms' frame rates quoted for it (37 to 39 a second, 39 to 42 with the crops hidden) have no record behind them.

- [ ] **The packaged game with this list:** packaged on 2026-11-08 (Shipping, `builds\mistward_castle`; every run of its `-Test` ok, the console reading `rd.WildRunSpeed` back), but no run went out to the farms, and whether `869` ran before it is not recorded: the crops' materials (the corn and potato plants', Bone Temple's and PureNature's) need the instanced-mesh usage. A Development package's log ("missing usage flag") would show it.
- [ ] **Hunting a fleeing animal:** struck once, a deer runs at 8.5 m/s and the Summoner's next bolts fell short of it; the test holds the animals before her. Whether a hunt reads well in play (bolts' reach against a fleeing deer, a sword against a hare at 4.2 m/s) is not measured.
- [ ] **An animal's return at the level's own wait** (120 s): measured with the wait at 45 s (another deer 45.5 s after the kill).
- [ ] **Walking into the farms:** running at 5x across them, 26 frames of 286 were over 100 ms (the grassland 11 of 225); the near chunks' crops (about 24,000 a chunk) are added in one go when a chunk comes near. At 1x not measured.
- [ ] **The ground's rows far off** read in a picture from above in one wheat field; the other crops' rows fade at a smaller distance (their rows are finer). Not judged across a whole farm region.
- [ ] **A thin dark line at the horizon** where the land's chunks end (seen in the fields' far picture): from before this list; not looked into.
- [ ] **The other towns' boards, dummies and panels** (Vel Morrath, Ashenreach, Graymourne): the code is shared; only Brokenspire was measured.
- [ ] **`rd.WildRunSpeed` in a packaged game:** set at the Shipping game's own console since 2026-11-08 (the package test's console run reads it back as 10); her run in the wilds at that speed has not been measured packaged.
- [ ] **The wilderness's sheer walls (2026-11-08, [wilderness.md](docs/levels/wilderness.md#the-sheer-walls-2026-11-08)):** the regions' mixing, the lakes' and ponds' banks and the roads' banks changed in `RDWildWorld.cpp`; measured without a game (`RDWildProbe`, `wild_seams.py`: no seams left round Brokenspire on the user's seed). Not yet run in play: `888` (all of it: every height moved a little; `ground7`, `ground8`, `quests`, `places` read the ground) and `884` (the town's way out and its roads), and the user's spot walked over in the game. Play on `brokenspire` ran the GPU out of memory again that day.
- [ ] **PR #27's review fixes, not yet run in play:** a killed animal rolled about its facing (`888 animals8` now measures the body's axes, `length_z` / `up_z`); the rain's drops two crossed planes in a field that keeps the world's axes (`rain8`: `pairs_crossed`, look at its pictures); `rd.WildRunSpeed` set as the console sets it, applied again to a new pawn, the hold checking the chunk's collision under her (`speed8`, and a hero switch at 10x); the streaming's measures counting chunks streamed while fast (`perf8`). The rain still follows the camera's place (a field round her), as since 2026-11-04.
- [ ] **The game's console (2026-11-08):** `884 console` not run on Brokenspire in the editor (play there ran the GPU out of memory); passed on the castle (`868 console`) and in the Shipping package in Brokenspire. Only the US layout's ` key was tried; no gamepad opens it; the lines typed are not kept between games.

## The list of 2026-11-04 ([docs/improvements7.txt](docs/improvements7.txt))

Built and tested (`884 list7`, `signs`, `gate`; `888 sky7`, `life7`, `ground7`, `music7`, `save`); still to test:

- [ ] **The weather over a long session:** the tests set each weather; the game's own changes every 4 to 9 minutes (the next one's time is checked) have not been watched for an hour.
- [ ] **The music's change after 5 to 10 minutes:** tested by asking for the next track at once and reading when the one after is due; no test has waited the minutes.
- [ ] **A named save loaded from the Load page,** and two saves of the same name (the second overwrites the first).
- [ ] **The town's rise and fall in the other towns** (Vel Morrath, Ashenreach, Graymourne): the code is the same; only Brokenspire was measured.

## Vel Morrath and its catacombs (2026-11-06, [docs/levels/vel_morrath.md](docs/levels/vel_morrath.md))

Built and tested (`884 holy`, `descend`; `868 catacombs -lv vel_morrath`; `888 world`, `towns`); still to test or do:

- [ ] **Its quests taken and turned in:** the archbishop's first quest is offered and its counter (`vel_morrath:enter`) reached 1 on the way down; none has been taken and turned in, and the tier, kill and boss counters below (`vel_morrath:tier`, `:kills`, `:boss`) have not been read after a fight.
- [ ] **Tiers 4 and 5 below:** the floors and stairs were measured for tiers 1 to 3 (0, -4.5, -9 m); 4 and 5 follow the same rule and have not been visited.
- [ ] **Monsters on the stairs:** monsters path over the tiles in two dimensions; one chasing her up or down a stair has not been watched.
- [ ] **A save in the catacombs loaded:** the save names the level and the place ("The Catacombs of Vel Morrath"); a load of it has not been run.
- [ ] **The plaza on the map:** its statues, fountain and shrines are not drawn; the cathedral and monastery borrow the temple's and chapel's pictures.
- [ ] **The catacombs' own looks:** tier 1 is the dungeon's stone and tier 3 and 4 are the castle's themes; only tier 2 (the crypt stone) is new. Bone-lined ossuary walls, niches and sarcophagi of their own are still to come.
- [ ] **The houses' stone:** in the morning light (08:00) the city reads blue-grey; it has not been pictured at noon.
- [ ] **The packaged game's city and catacombs played:** the package of 2026-11-06 goes down into the catacombs and out to the city and runs in each (no crash, no missing material in the Development package's log); the stair down from the cathedral, the deeper tiers and the way back have not been played in it.

## Ashenreach and The War Engine (2026-11-07, [docs/levels/ashenreach.md](docs/levels/ashenreach.md))

Built and tested (`884 forge`, `descendwar`); still to test or do:

- [ ] **The War Engine past its first hall:** tiers 2 to 5 (the brick, the dwarven halls, the mixed) and the props by their walls have not been visited; nor a governor (a tier's boss) fought.
- [ ] **Its quests taken and turned in**, the counters `war_engine:tier`, `:kills`, `:boss` read after a fight.
- [ ] **The machines fought:** each kind spawned and its clips measured playing; none fought. The borrowed warrior swings are a weapon's swings done empty-handed; the iron golem's rusted metal reads very dark.
- [ ] **The square's frame rate settled:** 5 to 7 just after the city was built round her; the casting hall 22 to 24.
- [ ] **Embers in the burned plain's air:** the swarms table has none for it.
- [ ] **The packaged game played:** the Shipping package of 2026-11-07 (`builds\graymourne`) goes down into `war_engine` (`-RDTownGo=dungeon:ashenreach`) and out to the city (`town:ashenreach`) and runs in each, no crash; `869` set the instanced-mesh usage on the city's new pieces (the barricade, the ore carts) and the skeletal-mesh usage on the iron golem's rusted iron. The Development package from the same cook (`builds\graymourne_dev`) logged no "missing usage flag" in the city or the first hall (the deeper tiers' pieces are checked only by `869`'s tables); no picture taken in it, and the gate, the deeper tiers and the way back have not been played in it.

## Heaven and its fortress (2026-11-09, [docs/levels/heaven.md](docs/levels/heaven.md))

Built and tested (`884 heaven`, `descendheaven`; `888 world`, `towns`, all with `-Light`); still to test or do:

- [ ] **The fortress past its first hall:** tiers 2 to 5 (the steel halls, the mixed) and the machines by the walls have not been visited; nor a tier's boss fought. The start hall keeps the castle's great-hall furniture (throne, carpet, banners, columns); its white floors read over-bright.
- [ ] **The defenders fought:** each kind spawned and its clips measured playing, a trooper's rounds measured reaching her; none fought hand to hand, the tank (a tank's idle for its walk and death) not seen moving or dying.
- [ ] **The towers' upper floors and the office blocks' upper storeys** are seen from outside only (no floors or stairs inside); no window is lit at night.
- [ ] **The cars' wheels do not turn** (each car one merged mesh); they turn back at a street's end by changing lanes at once; they do not stop at crossings or for townsfolk, only for her and each other.
- [ ] **The trades keep the town's signs and furnishing** (SMITHY, TAVERN, a hearth in a kitchen); the refugees about the gate wear the town's clothes; the square's lamps are fire baskets; the traffic lights show no changing light.
- [ ] **Its quests taken and turned in**, the counters `heaven:tier`, `:kills`, `:boss` read after a fight.
- [ ] **The city's frame rate settled:** 13 to 26 a second just after the city was built round her (a play window of 1280 x 720).
- [ ] **The packaged game:** `869` and `package_mistward.ps1` name `heaven_fortress` and its run down from the city (`-RDTownGo=dungeon:heaven`); not packaged yet. The merged meshes and the materials made by `908` need the instanced-mesh usage (`M_HV_Surface` has it).

## Kethrys Spire and its tower (2026-11-08b, [docs/levels/kethrys_spire.md](docs/levels/kethrys_spire.md))

Built and tested (`884 spire`, `descendspire`; `888 world`, `towns`, all with `-Light`); still to test or do:

- [ ] **The tower's dungeon past its first hall:** tiers 2 to 5 (the arcane halls, the castle's, the mixed) and the tower's props by the walls have not been visited; nor a tier's boss fought, nor its last boss's drop of Heaven's key. The start hall keeps the castle's great-hall furniture (throne, carpet, banners), now in darkened stone and violet light.
- [ ] **The casters fought:** each kind spawned and its clips measured playing; none fought, their bolts not seen in flight. The witches wear no parts; the elder witch is the witch at 1.1 times her size.
- [ ] **The tower's storeys walked:** the round storeys over the hall are seen from outside only (no floors or stair inside them).
- [ ] **Its quests taken and turned in**, the counters `kethrys:tier`, `:kills`, `:boss` read after a fight.
- [ ] **The city's frame rate settled:** 8 to 31 a second just after the city was built round her (a play window of 1280 x 720).
- [ ] **The apprentices meditate standing:** the two at a meditation chamber's circle stand in their idle; no seated or kneeling clip.
- [ ] **The packaged game:** `869` and `package_mistward.ps1` name `kethrys_spire` and its run down from the city (`-RDTownGo=dungeon:kethrysspire`); not packaged yet.

## Graymourne and its sewers (2026-11-07, [docs/levels/graymourne.md](docs/levels/graymourne.md))

Built and tested (`884 port`, `descendsewer`; `888 world`, `towns`); still to test or do:

- [x] **The harbour opens to the sea** (the list of 2026-11-11, `884 port11`): the sea round the port lifted to the harbour's water, no wall or blocker along the harbour, ramps out of it, a splash and rings in the water.
- [ ] **The open sea's limits:** the sea within 2.5 km of the port is lifted 74.8 m and eases back down from 2.5 to 40 km, so its face slopes there, at most 0.3 % by the curve (74.8 m over 37.5 km at the smoothstep's steepest, 1.5 times its mean; computed, not measured: not looked at from out at sea). Since 2026-11-12 she swims where it is deep and the splash, strokes and wading are heard (`884 swim12`). The water's displacement bends its face's normal only (per pixel: the coarse water mesh does not rise and fall); she does not dive; no boat or ship to board.
- [ ] **The coast round Graymourne in play:** measured by the probe and on six lines in play (20 m steps); not walked from the uplands down to the shore, and the beach beside the harbour not pictured.
- [ ] **The wrecks pictured:** placed by the sea wall (2 in the test), not yet in a picture.
- [ ] **The sewers past their first hall:** tiers 2 to 5 (the damp brick, the cistern's vaults, the mixed), their ramps down and the drowned things by the walls have not been visited; nor a warden (a tier's boss) fought. The start hall keeps the castle's great-hall furniture (throne, carpet, banners) and its warm torchlight.
- [ ] **Its quests taken and turned in**, the counters `sewers:tier`, `:kills`, `:boss` read after a fight.
- [ ] **The drowned fought:** each kind spawned and its clips measured playing; none fought. The fish-men's borrowed warrior swings are a weapon's swings done empty-handed.
- [ ] **The fog indoors:** the port's fog fills the houses and the Sluice House as it fills the streets.
- [ ] **The city's frame rate settled:** 2 to 16 just after the city was built round her.
- [ ] **The packaged game played:** the Shipping package of 2026-11-07 (`builds\graymourne`) goes down into `sewers` (`-RDTownGo=dungeon:graymourne`) and out to the port (`town:graymourne`) and runs in each, no crash; `869` set the instanced-mesh usage on the harbour's nets, wrecks, fish racks, boats and piers and the sewers' mud and drowned props (16 base materials). The Development package from the same cook (`builds\graymourne_dev`) logged no "missing usage flag" in the port or the first hall (the deeper tiers' pieces are checked only by `869`'s tables); no picture taken in it, and the sewer gate, the deeper tiers and the way back have not been played in it.

## PR #25's review (2026-11-07; checked and fixed 2026-11-08)

The review's finds, each checked (in play where it could be measured, else in the code) and fixed:

- [x] **The harbour's edges leaned: confirmed in play, fixed** (`884 port`: test_gm6 failed on it, test_gm10 passes). A walk-mesh vertex on a tile's edge took the tile on its +X / +Y side, so where the water lay +X or +Y of the land the walked ground fell up to 1.39 m within 1.5 m of the blocker and she slid 1.06 m down beside it (the piers' decks hid it there). A walked vertex on an edge is water now only if every tile it touches is (`RDTPTouching`): every blocker of the harbour level on its land side (152 quay edges, 170 pier-deck edges, none lower than 14 cm), she stops 0.45 m before the line on level ground on every way the quay has. The drawn bed drops behind the quay's stone face where a quay stands beyond the edge, and runs on to the edge elsewhere (PR #26's reviews: left on the grid it made a 1 m ramp in front of the face; dropped in front of the line it covered the face; lifted on every side it would have stood as a grass bank at the harbour's far side): the stone shows on every way in the edge pictures (`gm_edge_*`), the town wall straight out of the water on the far side (`gm_mouth`).
- [x] **The quest places' fallback, fixed**: a fixed point is held to the same flat, dry, off-road ground as far out as the quest asks (1.8 / 3 km): the den the nearest within 1.5 km, the tower the highest within 600 m of the first good ground; facing Brokenspire; else left there and logged. Not seen in a game yet (the test's games all find a place beside the road: `888 quests` test_s12).
- [x] **The wild quests offered before the wilds are ready, fixed**: a quest not yet taken waits for `IsWildReady()` as the accept does (a window of 0.13 to 0.54 s before); one taken, ready or done keeps its state meanwhile (PR #26's review).
- [x] **`-RDTownGo=catacombs` names Vel Morrath's catacombs** (it took the town's own dungeon when started in a city with one); its refusal and `dungeon:<town>`'s say why. Not run in a package since (the packaged test starts in Brokenspire, which has none, and goes the same way).
- [x] **The foundry's gate at `MistgateAt` unguarded: cannot happen**: the foundry's plan (`RDTownPlan.cpp` 688-691) always sets `MistgateAt` and `FoundryShell` runs only for a foundry (1100). Left as it is.
- [x] **The den's wolves by name**: the ripper dogs, else a wolf, hound or dog (case kept: not a werewolf or hellhound), else the place's own kind with a warning once a play (the generator's flag) (`888 quests` test_s12: four ripper dogs, no warning).
- [x] **A big plant entry is added in parts from where the last stopped** (`FWildBuild::InstAt`), not moved down each part. `888 build7`: the longest step 5.5 and 7.4 ms, at most 8.6 and 9.3 ms a frame in two runs after it (6.0 / 9.3 before, test_s5): the runs' own spread; the change not measurable apart.
- [x] **The dead loop** in `RDForge.cpp`'s `DoorRow` is a plain check of the row, its comment true (`884 forge` test_ar5: the same 19 forges and every piece count as ar4).

PR #26's second review, left open (small):

- [ ] **A quest panel opened before the wilds are ready keeps its LATER line** until it is opened again (`BuildTownLines` runs on a panel action or an opening): a window of 0.13 to 0.54 s at the start, a little longer after a trip down.
- [ ] **The den's pack by a word in the name**: with no ripper dog, a kind named "Dogman" or "WolfRider" would do (the first in the table, not the weakest), with no warning.

## The captain's wilderness quests (2026-11-07)

Built and tested (`888 quests`: their places, taken, the den's pack, the patrol found, turned in; `884 talk`: offered); still to test:

- [ ] **Played by hand:** the test kills the pack with a blow of 1e7 and puts her before the watchtower's door; nobody has walked out from the gate, followed the map to them and fought the four ripper dogs (tier 1, the den's size).
- [ ] **Saved and loaded with a quest taken:** the kills (`WildKilled`) and the find (`wild:patrol`) are saved with the game; a load in the middle of either has not been run.
- [ ] **Their places in other games:** they follow the roads, which leave by Brokenspire's gate (a new town each game); in the three test games the den was 1.82 to 1.84 km out beside the Ashenreach road (45 m from it) and the tower 2.98 to 2.99 km out off the Vel Morrath road, both on dry farmland. A game whose roads leave over ground too steep or wet for them falls back to fixed points (2 km north, 3.1 km north-east), never seen.

## The final boss (Aurorim, 2026-11-03)

Built and tested (`868`'s `finalboss`); still to test or do:

- [ ] **Coming back to an unslain final boss:** placed and not slain when she leaves the castle, he is set again once she sees a room of tier 5 on her way back (`bFinalRestorePending`); no test has left and come back.
- [ ] **The real share:** the test scales tier 5's share to 1 % (one set); a game reaches 50 % over about 16 of tier 5's 32 sets. Nobody has played that far.
- [ ] **His fight against each hero:** the balance trials have not fought him (tier 5's boss in them is its strongest kind); a starting Warrior dies in three of his blows. Trial him with the tier-5 kits ([docs/hero-balance.md](docs/hero-balance.md)).
- [ ] **A room with no wall free for the door:** the door goes against a wall of his room away from him; a room with none (never seen yet) leaves no door (the log says so). The castle's arch and its Escape menu still take her back.
- [ ] **The map:** the door has no mark of its own (his mark is the boss's).
- [ ] **Him in the packaged game:** the package of 2026-11-06 cooks him (his mesh, skeleton, material, texture and 9 clips are in the cook's list), but no run of it has reached tier 5 or met him.

## To do

- [ ] **New ground costs the drawing a frame:** a chunk is made in steps since 2026-11-07 (`888 build7`: the game thread's making at most 9.3 ms of a frame, its longest step 6 ms, against 14.7 ms for a whole chunk in one go; the 45 to 72 ms written here before were chunks she is put on, cooked at once). The frames with making are still 12 to 16 ms longer than those without, and stat unit's threads put that in the drawing: the render thread 40 to 62 ms against 29 to 33, the GPU 33 to 59 against 28 to 31 (the editor's view at 2440 x 1616 on the RTX 3060, flying 100 m/s over new ground). What of a new chunk costs the GPU (its shadows, the plants' first frames, the ground's upload) is not measured yet; measure it in the packaged game too.
- [ ] **Memory over a long walk:** back at the start after a 6 km walk out and back the editor held 470 to 670 MB more than when it began (the test allows 700); eight long journeys held flat. Measure hours of walking, and in the packaged game.
- [ ] Balance the heroes continent-wide: the first attempt covers Mistward Castle's five tiers only ([docs/hero-balance.md](docs/hero-balance.md#continent-wide-balancing-considerations)). The wilderness's tiers go by the distance from Brokenspire while her growth counts the castle's tiers she has opened; trials at each distance band, the wilderness's loot and the travel times are still to be done.

## Limits

What the wilderness does not do yet:

- **Caves have no inside:** a cave is its mouth among rocks.
- **Villages, camps and lone houses are empty:** their houses, tents and props stand, but nobody lives in them, and their houses are single pack pieces with no working doors, furniture or containers.
- **Monsters live only at spawn points and lairs:** between places there are only the animals that flee (deer, wolves, squirrels, hares: since the list of 2026-11-04), which never fight; no wandering monsters.
- **Birds and insects are effects round her** (Niagara flocks and swarms), not creatures: nothing hunts them and they do not land.
- **The weather has no lightning, puddles or wet ground:** the rain and snow are falling drops round the camera, the storm a darker sky, more rain and stronger wind.
- **Swimming at the face only:** she wades shallow water and swims deep water held at its face (2026-11-12); no diving, no drowning, nothing to stop her swimming far out to sea. The lava does no harm.
- [ ] **Swimming not yet tried in every water:** measured in Graymourne's harbour and the sea beyond it; a lake's and a river's deep water, a fall from a height into water, a death while swimming and a save made swimming were not tried.
- **Long walks:** the towns are 85 to 157 km apart, hours on foot; fast travel takes her to a town once she has found it.
- **One way into Mistward Castle:** only Brokenspire's Mistgate leads to it (and to its final boss); the three other cities (Vel Morrath, Ashenreach, Graymourne: cities of Brokenspire's size with their own people and quests since 2026-11-06/07) each lead to their own dungeon.
- **The light:** in the default morning (08:00) the land looks pale from a distance. The base colour buffer shows the ground's colours right; it is the low sun and the sky light.
- **The frame rate:** 10 to 48 frames a second (23 on average) in the editor's play window out there.
- **Memory in the editor:** one long play session that visited all 28 templates ran the machine short of memory (32 to 34 GB committed); the tests run in batches with the editor restarted between them. A walk with eight long journeys held flat at about 30.3 GB.
