# TODO

[README](README.md) · [The wilderness](docs/levels/wilderness.md) · [Brokenspire](docs/levels/brokenspire.md)

What is still to be tested and done, and the known limits. Written 2026-11-03 for the wilderness and the castle's final boss (the user's spec of 2026-11-03, [docs/wilderness.txt](docs/wilderness.txt)), merged that day in PR #16. Remove an item when a test shows it working or the work lands; add one when a limit is found.

## To test

Built and compiled, but no test has run it yet:

- [ ] **The hero menu's CONTINUE** (C or the pad's X): it loads the newest of the two saves. Test: a save written, the menu opened, CONTINUE, and she arrives where the save says.
- [ ] **The Escape menu's Load page loading a game:** the test checked the page's lines (which save, where, when; since the list of 2026-11-04 every named save among them); the load itself was tested through the code, not through the page's choice.
- [ ] **A load into another town:** she saved in Vel Morrath (or Ashenreach, or Graymourne), and the load builds that town first and puts her in it.
- [ ] **The autosaves on Quit and before the Mistgate** (`quit`, `castle`): the other autosaves (a place found, a town entered, before and after a journey) have run in the tests.
- [ ] **Coming back to life in the nearest found town** after a death in the wilds (`WildRespawnAt`): the nearest found town, not the nearest town, and it is loaded at once.
- [ ] **The teleport circle's journey to another town** (Brokenspire's circle to Vel Morrath's and back, and refused in a fight).
- [ ] **Ashenreach and Graymourne visited:** built as she nears them, their people their own, the maps switching in their walls (only Vel Morrath has been visited in a test).
- [ ] **The caldera's steam and the volcanoes' lava** seen in a picture from her view (the code places them; no picture has shown them yet).
- [ ] **The packaged game with the wilderness:** a Shipping build of `brokenspire` has not been made since the wilderness was added (worker threads, transient map textures and the save all behave differently packaged); then a walk out of the gate, a journey and a save and load in it, and its memory over a long walk.

## The list of 2026-11-04 ([docs/improvements7.txt](docs/improvements7.txt))

Built and tested (`884 list7`, `signs`, `gate`; `888 sky7`, `life7`, `ground7`, `music7`, `save`); still to test:

- [ ] **The weather over a long session:** the tests set each weather; the game's own changes every 4 to 9 minutes (the next one's time is checked) have not been watched for an hour.
- [ ] **The music's change after 5 to 10 minutes:** tested by asking for the next track at once and reading when the one after is due; no test has waited the minutes.
- [ ] **A named save loaded from the Load page,** and two saves of the same name (the second overwrites the first).
- [ ] **The town's rise and fall in the other towns** (Vel Morrath, Ashenreach, Graymourne): the code is the same; only Brokenspire was measured.

## The final boss (Aurorim, 2026-11-03)

Built and tested (`868`'s `finalboss`); still to test or do:

- [ ] **Coming back to an unslain final boss:** placed and not slain when she leaves the castle, he is set again once she sees a room of tier 5 on her way back (`bFinalRestorePending`); no test has left and come back.
- [ ] **The real share:** the test scales tier 5's share to 1 % (one set); a game reaches 50 % over about 16 of tier 5's 32 sets. Nobody has played that far.
- [ ] **His fight against each hero:** the balance trials have not fought him (tier 5's boss in them is its strongest kind); a starting Warrior dies in three of his blows. Trial him with the tier-5 kits ([docs/hero-balance.md](docs/hero-balance.md)).
- [ ] **A room with no wall free for the door:** the door goes against a wall of his room away from him; a room with none (never seen yet) leaves no door (the log says so). The castle's arch and its Escape menu still take her back.
- [ ] **The map:** the door has no mark of its own (his mark is the boss's).
- [ ] **The packaged game:** not built with him yet.

## To do

- [ ] **A chunk's making stutters:** the 5 ms budget a frame cannot split one chunk's work on the game thread (its mesh, collision setup, plants), measured at 45 to 72 ms: one long frame each time a chunk is made, every few seconds while she runs. Split it over frames (the ground first, then the plants).
- [ ] **Memory over a long walk:** back at the start after a 6 km walk out and back the editor held 470 to 670 MB more than when it began (the test allows 700); eight long journeys held flat. Measure hours of walking, and in the packaged game.
- [ ] Give the captain's two wilderness quests ("Wolves on the Mill Road", "The Lost Patrol") now that the gate is open: they still say they wait for it.
- [ ] Balance the heroes continent-wide: the first attempt covers Mistward Castle's five tiers only ([docs/hero-balance.md](docs/hero-balance.md#continent-wide-balancing-considerations)). The wilderness's tiers go by the distance from Brokenspire while her growth counts the castle's tiers she has opened; trials at each distance band, the wilderness's loot and the travel times are still to be done.

## Limits

What the wilderness does not do yet:

- **Caves have no inside:** a cave is its mouth among rocks.
- **Villages, camps and lone houses are empty:** their houses, tents and props stand, but nobody lives in them, and their houses are single pack pieces with no working doors, furniture or containers.
- **Monsters live only at spawn points and lairs:** between places there are only the animals that flee (deer, wolves, squirrels, hares: since the list of 2026-11-04), which never fight; no wandering monsters.
- **Birds and insects are effects round her** (Niagara flocks and swarms), not creatures: nothing hunts them and they do not land.
- **The weather has no lightning, puddles or wet ground:** the rain and snow are falling drops round the camera, the storm a darker sky, more rain and stronger wind.
- **No swimming:** she wades rivers and lakes on a floor under the water; an invisible wall keeps her out of the sea. The lava does no harm.
- **Long walks:** the towns are 85 to 157 km apart, hours on foot; fast travel takes her to a town once she has found it.
- **The small towns are simpler than Brokenspire:** no elder, scholar or captain, no quests of their own (their boards hold only old notices), a keep with no Mistgate.
- **The light:** in the default morning (08:00) the land looks pale from a distance. The base colour buffer shows the ground's colours right; it is the low sun and the sky light.
- **The frame rate:** 10 to 48 frames a second (23 on average) in the editor's play window out there.
- **Memory in the editor:** one long play session that visited all 28 templates ran the machine short of memory (32 to 34 GB committed); the tests run in batches with the editor restarted between them. A walk with eight long journeys held flat at about 30.3 GB.
