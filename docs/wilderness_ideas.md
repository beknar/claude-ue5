# The wilderness: ideas for later

[README](../README.md) · [The wilderness](levels/wilderness.md) · [TODO](../TODO.md)

These are suggestions for making the wilderness more engaging, taken from other open-world RPGs. They were written on 2026-11-14 after the TODO sweep, for later consideration. Since then the biomes' scenery ([docs/improvements13.txt](improvements13.txt), merged 2026-11-16) built parts of ideas 1 and 7, noted under each; the rest is not planned.

## Why it may feel flat

The wilds already have a lot in them:
- a point of interest about every 40 s, and the encounter director;
- twenty kinds of ruin and the hidden lairs;
- 34 structures with 25 quests;
- road travellers and their camps, and the farmsteads;
- hunting, swimming and the horse;
- the weather and day and night.

So the amount is probably not what is missing. Judged from what is built, not from play, three things may be:
- **Nothing pulls from afar:** from a hilltop little stands out as worth walking to.
- **Finds pay generic loot:** gold, a tier's items and materials. Few rewards are lasting or remembered.
- **Nothing changes:** a cleared camp or a killed beast leaves the world as it was.

## The ideas

Roughly in order of payoff for the work. Each notes what in the game it would build on.

### 1. Landmarks seen from afar (Breath of the Wild, Elden Ring)

- Each region gets one or two tall silhouettes of its own: a broken spire, a giant tree, a smoking crater, a beam of light at night.
- At night the camps show smoke and the houses lit windows.
- **The goal:** from any hilltop, three or four things worth walking to.
- **Builds on:** the far land (`RD/RDSkyFar.cpp`, drawn out to 80 km), the ruins' pieces (`RD/RDWildRuin12.cpp`), the camps (`RD/RDWild10.cpp`).
- **How to measure:** from sample hilltops in each region, count the landmarks within view in pictures.
- **Built since (2026-11-16):** a broken tower 182 m high at a fixed place in each 6 km square of the open lands, the nearest within 8 km standing (`WildLandmarkBiomes`), and the far storms and grass fires' smoke ([the wilderness](levels/wilderness.md), the biomes' scenery). Still open: a silhouette of each region's own, and the camps' smoke and lit windows at night.

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
- **Treasure maps:** found in ruins, each a picture of a spot that leads to a buried chest, recognised by its landmark (Red Dead Redemption 2, The Witcher 3).
- **Unique named items tied to places**, so "the sword from the drowned tower" is remembered.
- **Builds on:** the wild containers and their keys in the save (`RD/RDWildFarm11.cpp`), the items table and its tiers (`910`), the ruins' kinds.

### 5. Monster contracts you investigate (The Witcher 3)

- A town's board posts a named beast. She follows its tracks, signs and kills across the wilds to its lair, then fights it with a weakness learned on the way.
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

- Fewer random fights and more short scenes, for example:
  - a courier with a letter for her;
  - someone being chased;
  - a merchant whose cart has broken down;
  - a rival adventurer who keeps reaching places first.
- **Builds on:** the encounter director and its kinds (`912`, `920 events`, `SourceArt/wilderness/events11.json`), the road travellers (`916`).

### 9. Getting about

- **Waystones** she finds and lights, as the only fast travel.
- **Signposts** at road crossings naming the towns.
- **Danger shown on the map:** the roads coloured by tier, a skull near a roaming monster.
- **Climbing or gliding** (Breath of the Wild): it would change the most, but needs new animations. The most expensive item here.
- **Builds on:** the roads and their tiers (`FRDWildWorld::TierAt`), the map's travel (`WildTravelToTown`), the signs (`blender_numpy/bs_signs.py`).

## A first round, if chosen

1 to 4 together: they answer "why walk there" and "was it worth it", and reuse the far land, the watchtower, the monster tiers and the save. 5 and 6 next: they turn places into goals and consequences. 7 and 9 are bigger systems for later.

Each would be built the way the earlier lists were, in phases with a PR each. Each feature comes with a step in `888` and its part of [the wilderness's document](levels/wilderness.md).
