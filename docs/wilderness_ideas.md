# The wilderness: ideas for later

[README](../README.md) · [The wilderness](levels/wilderness.md) · [TODO](../TODO.md)

These are suggestions for making the wilderness more engaging, taken from other open-world RPGs. They were written on 2026-11-14 after the TODO sweep, for later consideration. Since then the biomes' scenery ([docs/improvements13.txt](improvements13.txt), merged 2026-11-16) built parts of ideas 1 and 7. Several others are partly in the game already, in the 25 structure quests (`SourceArt/wilderness/quests12.json`) and the encounter director's kinds (`SourceArt/wilderness/events11.json`). Each idea says what is in the game and what is still open; nothing more is planned.

## Why it may feel flat

The wilds already have a lot in them:
- a point of interest about every 40 s, and the encounter director;
- twenty kinds of ruin and the hidden lairs;
- 34 structures with 25 quests;
- road travellers and their camps, and the farmsteads;
- hunting, swimming and the horse;
- the weather and day and night.

Some of it already lasts: freed prisoners, cleared lairs and used points of interest stay done in the save (`WildKilled`), the lair clearing's choice reopens its road, and the frontier outpost and the legendary hunt give named rewards.

So the amount is probably not what is missing. Judged from what is built, not from play, three things may be:
- **Nothing pulls from afar:** from a hilltop little stands out as worth walking to.
- **Most finds pay generic loot:** gold, a tier's items and materials. Outside a few quests' rewards, little is lasting or remembered.
- **Little changes:** a cleared lair stays cleared, but the world round it does not change (no trader moves in, nothing is reclaimed).

## The ideas

Roughly in order of payoff for the work. Each notes what in the game it would build on.

### 1. Landmarks seen from afar (Breath of the Wild, Elden Ring)

- Each region gets one or two tall silhouettes of its own: a broken spire, a giant tree, a smoking crater, a beam of light at night.
- At night the camps show smoke and the houses lit windows.
- **The goal:** from any hilltop, three or four things worth walking to.
- **Builds on:** the far land (`RD/RDSkyFar.cpp`, drawn out to 80 km), the ruins' pieces (`RD/RDWildRuin12.cpp`), the camps (`RD/RDWild10.cpp`).
- **How to measure:** from sample hilltops in each region, count the landmarks within view in pictures.
- **Built since (2026-11-16):** a broken tower 182 m high at a fixed place in each 6 km square of the open lands, the nearest within 8 km standing (`WildLandmarkBiomes`), and the far storms and grass fires' smoke ([the wilderness](levels/wilderness.md), the biomes' scenery). Also in the game: the scenery's far pieces, never culled (a lone tree, a butte), and the places' landmarks (an ancient ruin, a giant's bones) in one cell in nine. Still open: a tall silhouette of each region's own, seen from its hilltops, and the camps' smoke and lit windows at night.

### 2. Lookout towers that reveal the map (Ubisoft's towers, Breath of the Wild)

- Climbing a tower uncovers its region's places on the map as unvisited marks.
- Exploring gets a rhythm: climb, look, pick a place, go.
- **Builds on:** the Old Watchtower and its stair (`916`), the map's fog and marks (`RD/RDWildMap.cpp`, `RD/RDWildHUD.cpp`), `rd.RevealMap`.

### 3. Named roaming monsters (Elden Ring's field bosses, Xenoblade)

- A few big named creatures per region walk set rounds, seen from a distance.
- They are well above the region's tier: learn where they walk and come back stronger.
- Some come out only at night or in storms.
- Each, once beaten, gives a unique item and a mark on the map.
- **Builds on:**
  - the monsters by tier and the wilds' bands (`RD/RDTier25.cpp`);
  - the elephant's walked round (`RD/RDWildSite12.cpp`);
  - the kills kept in the save (`WildKilled`);
  - the weather and the hour (`RD/RDSky.cpp`).

### 4. Rewards that last

- **Region collectibles:** small finds scattered through each region, traded for something permanent: more carrying space, hit points or a skill point (Breath of the Wild's Korok seeds).
- **Treasure maps:** found in ruins, each a picture of a spot that leads to a buried chest, recognised by its landmark (Red Dead Redemption 2, The Witcher 3). Two quests already work this way: "The lost ruin" (a half-burned map that leads to a ruin) and "The buried cache" (a riddle that leads to a crate dug up); the open part is maps found loose in ruins, as pictures, in any number.
- **Unique named items tied to places**, so "the sword from the drowned tower" is remembered.
- **Builds on:** the wild containers and their keys in the save (`RD/RDWildFarm11.cpp`), the items table and its tiers (`910`), the ruins' kinds, the quests' stages (`do=collect`, `do=goto` with `at=trail`, `RD/RDWildQuest12.cpp`).

### 5. Monster contracts you investigate (The Witcher 3)

- A town's board posts a named beast. She follows its tracks, signs and kills across the wilds to its lair, then fights it with a weakness learned on the way.
- **Already in the game:** the "Monster bounty" quest (a bounty hunter posts a named beast, the Grey Ravager; she follows its kills along a trail to it, with a twist after) and "The legendary hunt" (bait gathered, a trap set, rival hunters). Still open: the weakness learned on the way, and contracts posted on the towns' boards, more than one beast.
- **Builds on:** the quest boards and quest stages (`RD/RDWildQuest12.cpp`), the lairs (`RD/RDWildLair12.cpp`), the hunted animals (`RD/RDWild8.cpp`).

### 6. Camps cleared that change the world (Far Cry's outposts, The Witcher 3's resettled villages)

- A bandit camp or monster nest, once cleared, becomes a friendly waypoint: a trader, a bed, a fast-travel point.
- A few days later, people move into the ruin nearby.
- The map shows each region's share reclaimed.
- **Builds on:** the lairs and their kept kills, the structures' quests, the farmsteads' families (`RD/RDWildFarm.cpp`), the save.

### 7. Regions that need preparing for (Breath of the Wild)

- Snow fields drain her slowly without warm gear or a hot meal; deserts do the same by day; marshes poison.
- Cooking with the regions' own herbs and game gives resistance and buffs.
- Biomes would matter, and gardening, hunting and the oven would have a reason.
- **Builds on:** the biome table (`SourceArt/wilderness/biomes.json`), the gardens' ingredients and the oven (`890`), food effects, the armour table.
- **Built since (2026-11-16):** the cold in the arctic, glaciers, peaks and tundras (away from a fire, a town or a shelter it bites her past 90 s), thin air on the heights, and the marshes' mud and bogs. Still open: warm gear, a hot meal against the cold, the deserts by day, cooking for resistance.

### 8. Encounters on the road with a story (Skyrim, Red Dead Redemption 2)

- More short scenes among the fights. The director already sends talking travellers (a courier, a pilgrim, a pedlar, a lost hunter, a refugee: `roam_courier` and the others in `events11.json`), and the legendary hunt has rival hunters. Still open, for example:
  - a courier with a letter for her by name, from someone she has met;
  - someone being chased;
  - a merchant whose cart has broken down;
  - a rival adventurer who keeps reaching places first, across the wilds, not one quest.
- **Builds on:** the encounter director and its kinds (`912`, `920 events`, `SourceArt/wilderness/events11.json`), the road travellers (`916`).

### 9. Getting about

- **Waystones** she finds and lights, travelled to beside the towns (the map's travel to found towns stays: `888`'s travel step, the respawn in the nearest found town and the long quests rely on it).
- **Signposts** at road crossings naming the towns: the crossroads are found already (`MakeCrossroads`, 155 in a world), and kinds stand at them (`crossroads_notice`, which names the nearest structure; `crossroads_shrine`; `crossroads_gibbet`), with a signpost piece (`s12_signpost`): the open part is a post at each naming the towns down each road.
- **Danger shown on the map:** the roads coloured by tier, a skull near a roaming monster.
- **Climbing or gliding** (Breath of the Wild): it would change the most, but needs new animations. The most expensive item here.
- **Builds on:** the roads and their tiers (`FRDWildWorld::TierAt`), the crossroads and `place=crossroads` (`RD/RDWildWorld.cpp`), the map's travel (`WildTravelToTown`), the signs (`blender_numpy/bs_signs.py`).

## A first round, if chosen

1 to 4 together: they answer "why walk there" and "was it worth it", and reuse the far land, the watchtower, the monster tiers and the save. 5 and 6 next: they turn places into goals and consequences. 7 and 9 are bigger systems for later.

Each would be built the way the earlier lists were, in phases with a PR each. Each feature comes with a step in `888` and its part of [the wilderness's document](levels/wilderness.md).
