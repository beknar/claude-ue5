# Performance

The packaged game's frame rate in every city and every biome, measured before and after the list of 2026-11-22 ([improvements16.txt](improvements16.txt)).

Notes on reading the tables:

- **Fixed seeds:** the runs use the world's and Brokenspire's seeds fixed for a measuring run (16016), and the later runs replay BEFORE's places exactly (`-RDPerfPlaces`), so each row is the same place, hour and view in every section.
- **One resolution:** the runs are at the desktop's own (3840 x 2160). The first BEFORE run also measured 1920 x 1080 and read nearly the same: the engine's default screen percentage (`r.ScreenPercentage` 0, chosen by the display's resolution) renders a 4K screen at about half its width and height, so both draw about 1920 x 1080 before the upscale.
- **Quality:** every group at Epic (3); the overall level reads -1 because the resolution quality is 0 (the screen percentage left to the engine). Vertical sync off and no frame cap, whatever the player's settings hold.
- **The first BEFORE run was measured again** (2026-11-22, 23:37) after PR #111's review fixed the measuring run: the hour now held, the run's turn at most once a second, the picture taken after the measure, a row never filed for another place.
- **A biome with no dry ground at its nearest site** is measured at its next. The glacial biome's next site is by Kethrys Spire.
- **The canyon networks' run is not measured:** she was moved 13 km in a frame during it (put back at Brokenspire), and the run refuses such a row.
- **After the changes** (AFTER, 2026-11-25, the final Shipping package with every phase's content in it): the two worst places gained the most: the temperate autumn forests 17.9 to 21.9 FPS (+22 %, the GPU 55 to 44.5 ms a frame) and the volcanoes 13.8 to 16.5 (+20 %). Brokenspire's square at noon and Heaven's square gained 6 to 8 %. Most other places are within ±5 % of BEFORE, a few below it (the table's own figures: the wetlands standing -11 %, running -0 %; the castle's first hall -7 %; the plains -5 to -6 %; the geothermal caldera -5 to -6 %). MID measured the level-of-detail work alone. The content of phases 8 to 27 came after it: the caves, Heaven's streets, people, traffic and storeys, and the fortress's new tiers. Against MID most places read the same or a few % lower (the volcanoes 17.4 to 16.5, the castle's first hall 36.8 to 34.7, the wetlands 26.2 to 24.7). The largest falls are Ashenreach at midnight (its street 32.1 to 27.9, -13 %; its square 32.6 to 29.4, -10 %). The fortress's first hall rose (33.6 to 36.3, +8 %), and the autumn forests kept their gain (21.6 to 21.9).
- **The worst places before the changes:** the temperate autumn forests (17.9 FPS, the GPU 55 ms a frame) and the volcanoes (13.8 FPS, the game thread 34 ms a frame). The cities read 23 to 32 FPS, the GPU 30 to 41 ms a frame; the castle's first hall 37.5, the fortress's 34.2.

## BEFORE LIST16 changes

Written 2026-11-22 23:37 from the Shipping package's `-RDPerf` run (`pipeline/perf_mistward.ps1`, `RD/RDList16.cpp`), the editor closed, full screen: each city's square and a street about 100 m off it at noon and at midnight; each biome at its nearest site to Brokenspire at noon, standing, then running 30 s from there; the castle's and Heaven's fortress's first hall. Each standing place settled 20 s after the world round her was built, then measured until 15 s and 300 frames had passed (at most 45 s), clear weather, her HUD hidden, facing the longest clear line from her eyes. FPS is the mean over the frames; p95 and p99 are the 95th and 99th percentile frame times in ms; the thread times are the engine's own (stat unit's game, draw, RHI and GPU) averaged over the frames (0 where the build does not keep them). A biome whose name differs from the one under her feet was measured where the put-down found ground.

### 3840x2160

Measured 2026-11-22 22:42 on NVIDIA GeForce RTX 3060, overall quality level -1 (0 low to 3 epic) (by group: res0 view3 aa3 shadow3 gi3 refl3 pp3 tex3 fx3 foliage3 shading3), screen percentage 0, vertical sync off and no frame cap.

| Place | FPS | p95 ms | p99 ms | Game ms | Draw ms | RHI ms | GPU ms | Frames | Where (km) | Biome there |
|---|---|---|---|---|---|---|---|---|---|---|
| Brokenspire: square, noon | 24.7 | 45.4 | 46.4 | 16.8 | 7.9 | 10.7 | 39.2 | 371 | 0.0, -0.1 | farms |
| Brokenspire: square, midnight | 31.9 | 32.5 | 33.0 | 14.1 | 6.7 | 9.0 | 30.1 | 479 | 0.0, -0.1 | farms |
| Brokenspire: street, noon | 25.7 | 43.7 | 44.5 | 15.7 | 7.4 | 10.0 | 37.6 | 387 | 0.0, -0.2 | farms |
| Brokenspire: street, midnight | 33.1 | 31.5 | 32.1 | 13.8 | 6.4 | 8.7 | 29.0 | 496 | 0.0, -0.2 | farms |
| Ashenreach: square, noon | 25.0 | 44.3 | 45.3 | 18.0 | 8.0 | 11.8 | 38.7 | 376 | 35.0, -0.1 | burned plain |
| Ashenreach: square, midnight | 29.2 | 35.4 | 36.1 | 15.9 | 6.7 | 10.3 | 33.2 | 438 | 35.0, -0.1 | burned plain |
| Ashenreach: street, noon | 25.0 | 42.6 | 43.7 | 16.4 | 7.6 | 10.5 | 38.7 | 376 | 35.0, -0.2 | burned plain |
| Ashenreach: street, midnight | 26.7 | 38.7 | 39.6 | 15.0 | 6.5 | 9.4 | 36.3 | 401 | 35.0, -0.2 | burned plain |
| Graymourne: square, noon | 25.6 | 44.2 | 45.5 | 13.2 | 7.1 | 10.2 | 37.9 | 384 | 99.0, -0.0 | coastal regions |
| Graymourne: square, midnight | 28.8 | 36.0 | 36.7 | 11.5 | 6.1 | 9.0 | 33.5 | 432 | 99.0, -0.0 | coastal regions |
| Graymourne: street, noon | 27.8 | 40.2 | 40.6 | 12.1 | 6.6 | 9.8 | 34.8 | 418 | 98.9, -0.0 | coastal regions |
| Graymourne: street, midnight | 30.5 | 34.1 | 34.9 | 10.8 | 5.8 | 8.5 | 31.6 | 459 | 98.9, -0.0 | coastal regions |
| Vel Morrath: square, noon | 25.1 | 44.5 | 45.3 | 16.6 | 7.3 | 11.4 | 38.8 | 377 | 27.5, 37.6 | mountains |
| Vel Morrath: square, midnight | 28.1 | 36.9 | 37.9 | 14.7 | 6.3 | 10.3 | 34.5 | 421 | 27.5, 37.6 | mountains |
| Vel Morrath: street, noon | 26.7 | 41.7 | 42.4 | 17.8 | 7.8 | 11.9 | 36.1 | 401 | 27.5, 37.7 | mountains |
| Vel Morrath: street, midnight | 31.9 | 32.6 | 33.6 | 14.7 | 6.7 | 10.4 | 30.1 | 479 | 27.5, 37.7 | mountains |
| Kethrys Spire: square, noon | 24.5 | 45.0 | 45.9 | 20.1 | 8.2 | 11.0 | 39.5 | 368 | 76.3, -35.0 | glacial |
| Kethrys Spire: square, midnight | 27.7 | 38.5 | 39.9 | 19.8 | 9.3 | 11.2 | 34.7 | 416 | 76.3, -35.0 | glacial |
| Kethrys Spire: street, noon | 27.5 | 39.6 | 40.4 | 18.4 | 7.5 | 9.4 | 35.1 | 413 | 76.3, -35.1 | glacial |
| Kethrys Spire: street, midnight | 31.9 | 32.5 | 33.4 | 16.1 | 6.3 | 8.7 | 30.2 | 478 | 76.3, -35.1 | glacial |
| Heaven: square, noon | 23.9 | 50.1 | 54.1 | 20.9 | 8.4 | 13.3 | 40.7 | 360 | 57.1, -55.5 | volcanoes |
| Heaven: square, midnight | 26.5 | 41.9 | 53.7 | 19.0 | 7.0 | 12.1 | 36.7 | 398 | 57.1, -55.5 | volcanoes |
| Heaven: street, noon | 26.9 | 43.8 | 49.2 | 19.0 | 7.9 | 11.9 | 36.1 | 404 | 57.1, -55.6 | volcanoes |
| Heaven: street, midnight | 30.4 | 36.0 | 45.2 | 18.2 | 7.2 | 11.5 | 31.7 | 456 | 57.1, -55.6 | volcanoes |
| grasslands | 28.0 | 37.7 | 38.7 | 9.3 | 5.2 | 6.8 | 35.0 | 420 | 4.5, -0.4 | grasslands |
| grasslands: running | 28.0 | 37.9 | 39.2 | 10.4 | 5.5 | 7.3 | 34.9 | 840 | 4.4, -0.3 (105 m run) | grasslands |
| meadows | 27.8 | 38.5 | 39.3 | 9.6 | 5.3 | 7.1 | 35.0 | 417 | 6.4, 5.9 | meadows |
| meadows: running | 31.2 | 36.2 | 38.0 | 9.5 | 5.3 | 6.8 | 31.2 | 936 | 6.4, 6.0 (104 m run) | meadows |
| farms | 27.6 | 38.3 | 39.2 | 10.0 | 5.4 | 7.8 | 35.2 | 414 | 1.5, -1.2 | farms |
| farms: running | 27.9 | 38.4 | 39.6 | 10.1 | 5.7 | 7.5 | 35.0 | 837 | 1.6, -1.1 (105 m run) | farms |
| savannahs | 32.9 | 32.2 | 32.8 | 8.0 | 5.0 | 6.2 | 29.4 | 494 | -6.8, -17.3 | savannahs |
| savannahs: running | 32.4 | 33.4 | 35.1 | 8.0 | 5.1 | 6.2 | 29.9 | 972 | -6.6, -17.3 (105 m run) | savannahs |
| hills | 29.5 | 35.7 | 36.6 | 8.4 | 5.0 | 6.8 | 33.1 | 444 | -9.7, 5.3 | hills |
| hills: running | 32.1 | 34.6 | 35.9 | 8.5 | 5.2 | 6.7 | 30.3 | 964 | -9.7, 5.3 (25 m run) | hills |
| mountains | 35.5 | 29.8 | 30.4 | 4.2 | 4.4 | 5.1 | 27.3 | 532 | 10.5, 0.4 | mountains |
| mountains: running | 33.3 | 32.7 | 33.7 | 4.2 | 4.5 | 5.2 | 29.2 | 999 | 10.5, 0.5 (104 m run) | mountains |
| tundras | 27.7 | 37.8 | 38.9 | 17.5 | 5.8 | 11.7 | 35.0 | 416 | 59.3, -10.2 | tundras |
| tundras: running | 27.2 | 39.5 | 44.3 | 19.3 | 6.5 | 13.1 | 35.5 | 815 | 59.4, -10.2 (105 m run) | tundras |
| plains | 28.6 | 37.0 | 37.9 | 14.5 | 6.1 | 9.6 | 34.0 | 429 | 0.7, -8.0 | plains |
| plains: running | 28.5 | 37.1 | 37.9 | 14.1 | 6.0 | 9.1 | 34.1 | 856 | 0.8, -8.0 (105 m run) | plains |
| pine forests | 28.7 | 36.7 | 37.2 | 10.1 | 5.4 | 7.3 | 33.9 | 431 | 31.2, -16.9 | pine forests |
| pine forests: running | 28.2 | 39.0 | 40.5 | 10.7 | 5.9 | 7.5 | 34.5 | 846 | 31.3, -17.0 (105 m run) | pine forests |
| temperate autumn forests | 17.9 | 63.7 | 64.5 | 11.7 | 5.6 | 7.0 | 55.2 | 300 | 13.3, -38.6 | temperate autumn forests |
| temperate autumn forests: running | 17.7 | 65.7 | 68.9 | 13.2 | 5.8 | 7.5 | 55.6 | 531 | 13.3, -38.6 (105 m run) | temperate autumn forests |
| marshes | 27.9 | 37.9 | 39.0 | 7.8 | 5.1 | 7.0 | 35.0 | 419 | 24.6, 13.0 | marshes |
| marshes: running | 28.4 | 37.5 | 38.6 | 8.3 | 5.4 | 7.1 | 34.3 | 852 | 24.7, 13.0 (90 m run) | marshes |
| wetlands | 27.9 | 39.7 | 40.6 | 9.2 | 5.3 | 7.3 | 34.9 | 419 | 20.7, 18.4 | wetlands |
| wetlands: running | 27.5 | 39.8 | 41.3 | 9.4 | 5.5 | 7.3 | 35.5 | 824 | 20.7, 18.5 (90 m run) | wetlands |
| mountains and peaks | 36.8 | 29.0 | 29.9 | 3.7 | 4.5 | 5.1 | 26.2 | 552 | -15.1, -17.9 | mountains and peaks |
| mountains and peaks: running | 37.4 | 28.5 | 29.5 | 4.1 | 4.7 | 5.2 | 25.7 | 1121 | -15.1, -17.8 (71 m run) | mountains and peaks |
| volcanoes | 13.8 | 78.7 | 82.7 | 34.3 | 17.2 | 18.8 | 25.5 | 300 | 61.6, -55.5 | volcanoes |
| volcanoes: running | 14.5 | 81.3 | 89.9 | 31.4 | 14.9 | 17.1 | 26.1 | 436 | 61.5, -55.4 (106 m run) | volcanoes |
| coastal regions | 29.1 | 36.6 | 37.7 | 6.6 | 5.2 | 6.4 | 33.2 | 437 | -30.8, -1.3 | coastal regions |
| coastal regions: running | 29.4 | 36.5 | 38.1 | 6.7 | 5.4 | 6.1 | 32.9 | 884 | -30.7, -1.2 (106 m run) | coastal regions |
| arctic regions | 27.8 | 38.1 | 38.7 | 8.0 | 5.0 | 8.0 | 35.0 | 418 | 84.0, 19.0 | arctic regions |
| arctic regions: running | 27.4 | 38.8 | 39.7 | 7.9 | 5.0 | 7.8 | 35.5 | 823 | 83.9, 19.1 (105 m run) | arctic regions |
| canyons | 30.9 | 34.1 | 35.0 | 13.9 | 6.0 | 8.9 | 31.5 | 464 | -8.0, -8.7 | canyons |
| canyons: running | 31.7 | 33.5 | 34.5 | 13.9 | 6.0 | 8.6 | 30.7 | 951 | -8.1, -8.8 (105 m run) | canyons |
| mesas | 32.0 | 33.0 | 34.3 | 12.7 | 5.8 | 8.7 | 30.3 | 480 | -16.4, 4.6 | mesas |
| mesas: running | 31.4 | 34.7 | 36.1 | 13.7 | 5.9 | 9.1 | 30.9 | 943 | -16.3, 4.6 (104 m run) | mesas |
| canyon networks | 39.3 | 26.7 | 27.2 | 10.4 | 5.2 | 7.1 | 24.4 | 589 | -13.0, -2.9 | canyon networks |
| canyon networks: running | skipped: not measured: she was moved 13323 m in a frame | | | | | | | | | |
| cold steppes | 31.0 | 34.0 | 34.9 | 8.7 | 5.2 | 7.9 | 31.3 | 466 | 39.8, 34.8 | cold steppes |
| cold steppes: running | 28.8 | 37.1 | 38.3 | 9.1 | 5.5 | 8.0 | 33.8 | 863 | 39.9, 34.7 (105 m run) | cold steppes |
| highland moorland | 32.1 | 32.9 | 33.4 | 10.9 | 5.7 | 9.9 | 30.1 | 483 | 26.6, 19.2 | highland moorland |
| highland moorland: running | 32.0 | 33.2 | 34.2 | 11.7 | 5.9 | 9.4 | 30.3 | 961 | 26.7, 19.3 (105 m run) | highland moorland |
| boreal pine forest | 27.4 | 38.4 | 39.3 | 11.7 | 5.6 | 8.1 | 35.4 | 411 | 52.6, -23.5 | boreal pine forest |
| boreal pine forest: running | 26.7 | 39.6 | 40.9 | 11.6 | 5.7 | 7.8 | 36.4 | 800 | 52.5, -23.5 (105 m run) | boreal pine forest |
| temperate aspen | 29.7 | 36.2 | 36.8 | 9.1 | 5.4 | 7.2 | 32.5 | 447 | 31.2, -10.3 | temperate aspen |
| temperate aspen: running | 30.0 | 36.2 | 37.5 | 8.9 | 5.3 | 6.8 | 32.3 | 900 | 31.3, -10.2 (105 m run) | temperate aspen |
| volcanic tundra | 28.2 | 37.4 | 38.3 | 17.4 | 6.0 | 11.2 | 34.4 | 424 | 61.5, -0.8 | volcanic tundra |
| volcanic tundra: running | 28.5 | 37.2 | 38.3 | 17.9 | 6.4 | 11.8 | 34.0 | 855 | 61.6, -0.8 (101 m run) | volcanic tundra |
| burned plain | 30.9 | 34.3 | 35.0 | 8.7 | 5.1 | 6.7 | 31.4 | 464 | 37.5, 0.0 | burned plain |
| burned plain: running | 31.3 | 34.4 | 35.4 | 8.8 | 5.2 | 6.9 | 31.0 | 939 | 37.5, 0.1 (105 m run) | burned plain |
| geothermal caldera | 29.2 | 35.8 | 36.5 | 9.5 | 5.1 | 7.4 | 33.4 | 439 | 27.8, -43.8 | geothermal caldera |
| geothermal caldera: running | 27.7 | 39.6 | 40.5 | 10.3 | 5.5 | 7.5 | 35.3 | 830 | 27.9, -43.8 (105 m run) | geothermal caldera |
| glacial | 25.1 | 43.9 | 45.0 | 19.2 | 7.9 | 10.6 | 38.7 | 377 | 76.3, -35.0 | glacial |
| glacial: running | 25.9 | 43.6 | 45.0 | 19.3 | 7.8 | 10.3 | 37.4 | 778 | 76.3, -35.1 (68 m run) | glacial |
| taigas | 25.8 | 41.0 | 41.6 | 10.7 | 5.5 | 7.8 | 37.7 | 387 | 67.6, 20.8 | taigas |
| taigas: running | 25.6 | 42.1 | 43.3 | 13.5 | 6.7 | 9.7 | 37.9 | 768 | 67.7, 20.9 (105 m run) | taigas |
| rocky coastal | 40.0 | 26.7 | 27.4 | 6.9 | 4.6 | 6.0 | 24.0 | 601 | -22.9, -13.1 | rocky coastal |
| rocky coastal: running | 38.7 | 27.8 | 28.9 | 6.9 | 4.7 | 6.0 | 24.8 | 1160 | -22.8, -13.1 (105 m run) | rocky coastal |
| mistward_castle: first hall | 37.5 | 27.8 | 28.5 | 5.0 | 4.8 | 5.9 | 25.8 | 563 | 0.0, 0.0 | - |
| heaven_fortress: first hall | 34.2 | 30.4 | 30.8 | 4.9 | 4.8 | 5.8 | 28.3 | 513 | 0.0, 0.0 | - |

## MID LIST16 changes

Written 2026-11-23 04:10 from the Shipping package's `-RDPerf` run (`pipeline/perf_mistward.ps1`, `RD/RDList16.cpp`), the editor closed, full screen: each city's square and a street about 100 m off it at noon and at midnight; each biome at its nearest site to Brokenspire at noon, standing, then running 30 s from there; the castle's and Heaven's fortress's first hall. Each standing place settled 20 s after the world round her was built, then measured until 15 s and 300 frames had passed (at most 45 s), clear weather, her HUD hidden, facing the longest clear line from her eyes. FPS is the mean over the frames; p95 and p99 are the 95th and 99th percentile frame times in ms; the thread times are the engine's own (stat unit's game, draw, RHI and GPU) averaged over the frames (0 where the build does not keep them). A biome whose name differs from the one under her feet was measured where the put-down found ground.

### 3840x2160

Measured 2026-11-23 03:16 on NVIDIA GeForce RTX 3060, overall quality level -1 (0 low to 3 epic) (by group: res0 view3 aa3 shadow3 gi3 refl3 pp3 tex3 fx3 foliage3 shading3), screen percentage 0, vertical sync off and no frame cap.

| Place | FPS | p95 ms | p99 ms | Game ms | Draw ms | RHI ms | GPU ms | Frames | Where (km) | Biome there | Change |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Brokenspire: square, noon | 26.2 | 43.0 | 44.1 | 19.1 | 8.7 | 10.6 | 36.6 | 394 | 0.0, -0.1 | farms | +6 % |
| Brokenspire: square, midnight | 33.5 | 31.4 | 32.4 | 14.4 | 6.5 | 8.7 | 28.5 | 503 | 0.0, -0.1 | farms | +5 % |
| Brokenspire: street, noon | 27.8 | 41.1 | 41.8 | 13.2 | 6.4 | 8.2 | 34.8 | 417 | 0.0, -0.2 | farms | +8 % |
| Brokenspire: street, midnight | 34.8 | 30.4 | 31.4 | 12.6 | 6.1 | 8.0 | 27.4 | 523 | 0.0, -0.2 | farms | +5 % |
| Ashenreach: square, noon | 26.5 | 42.3 | 44.0 | 17.0 | 7.6 | 10.7 | 36.4 | 398 | 35.0, -0.1 | burned plain | +6 % |
| Ashenreach: square, midnight | 32.6 | 32.3 | 32.7 | 15.3 | 6.5 | 9.2 | 29.4 | 489 | 35.0, -0.1 | burned plain | +12 % |
| Ashenreach: street, noon | 26.1 | 41.5 | 42.1 | 15.8 | 6.9 | 9.1 | 37.0 | 392 | 35.0, -0.2 | burned plain | +4 % |
| Ashenreach: street, midnight | 32.1 | 32.3 | 33.0 | 14.1 | 6.4 | 8.2 | 29.9 | 482 | 35.0, -0.2 | burned plain | +20 % |
| Graymourne: square, noon | 25.2 | 45.1 | 46.3 | 11.3 | 6.3 | 8.9 | 38.3 | 378 | 99.0, -0.0 | coastal regions | -2 % |
| Graymourne: square, midnight | 29.6 | 35.1 | 35.7 | 10.2 | 5.5 | 7.8 | 32.5 | 444 | 99.0, -0.0 | coastal regions | +3 % |
| Graymourne: street, noon | 27.5 | 40.8 | 41.9 | 10.9 | 6.1 | 8.3 | 35.1 | 413 | 98.9, -0.0 | coastal regions | -1 % |
| Graymourne: street, midnight | 30.4 | 34.2 | 34.6 | 9.8 | 5.2 | 7.6 | 31.7 | 456 | 98.9, -0.0 | coastal regions | -0 % |
| Vel Morrath: square, noon | 25.4 | 44.2 | 45.1 | 15.5 | 6.5 | 10.4 | 38.0 | 382 | 27.5, 37.6 | mountains | +1 % |
| Vel Morrath: square, midnight | 28.5 | 36.5 | 37.5 | 13.6 | 6.1 | 9.3 | 33.8 | 427 | 27.5, 37.6 | mountains | +1 % |
| Vel Morrath: street, noon | 27.6 | 40.7 | 41.3 | 14.8 | 7.0 | 10.4 | 34.8 | 415 | 27.5, 37.7 | mountains | +3 % |
| Vel Morrath: street, midnight | 33.0 | 31.6 | 32.1 | 13.7 | 6.3 | 9.5 | 28.9 | 496 | 27.5, 37.7 | mountains | +3 % |
| Kethrys Spire: square, noon | 24.8 | 44.7 | 45.9 | 18.9 | 7.2 | 9.5 | 39.0 | 372 | 76.3, -35.0 | glacial | +1 % |
| Kethrys Spire: square, midnight | 29.1 | 35.7 | 36.4 | 16.3 | 6.6 | 8.4 | 33.1 | 437 | 76.3, -35.0 | glacial | +5 % |
| Kethrys Spire: street, noon | 27.7 | 39.5 | 40.0 | 16.4 | 6.6 | 8.1 | 34.8 | 416 | 76.3, -35.1 | glacial | +1 % |
| Kethrys Spire: street, midnight | 31.8 | 32.7 | 33.6 | 14.8 | 5.7 | 7.7 | 30.1 | 478 | 76.3, -35.1 | glacial | -0 % |
| Heaven: square, noon | 26.9 | 41.5 | 44.7 | 20.0 | 7.5 | 11.4 | 35.6 | 403 | 57.1, -55.5 | volcanoes | +13 % |
| Heaven: square, midnight | 29.5 | 37.7 | 39.7 | 18.5 | 6.5 | 10.8 | 32.5 | 442 | 57.1, -55.5 | volcanoes | +11 % |
| Heaven: street, noon | 29.0 | 37.7 | 39.9 | 18.3 | 7.2 | 10.6 | 32.9 | 436 | 57.1, -55.6 | volcanoes | +8 % |
| Heaven: street, midnight | 30.7 | 35.1 | 36.7 | 17.2 | 6.4 | 9.6 | 31.1 | 461 | 57.1, -55.6 | volcanoes | +1 % |
| grasslands | 28.1 | 37.6 | 38.1 | 9.4 | 5.2 | 6.6 | 34.5 | 422 | 4.5, -0.4 | grasslands | +0 % |
| grasslands: running | 28.3 | 37.3 | 38.4 | 10.4 | 5.7 | 7.4 | 34.2 | 851 | 4.4, -0.3 (105 m run) | grasslands | +1 % |
| meadows | 27.4 | 39.1 | 40.1 | 9.5 | 5.4 | 6.6 | 35.3 | 411 | 6.4, 5.9 | meadows | -1 % |
| meadows: running | 31.0 | 36.2 | 38.1 | 9.5 | 5.3 | 6.7 | 31.2 | 929 | 6.4, 6.0 (104 m run) | meadows | -1 % |
| farms | 28.0 | 38.1 | 39.0 | 9.9 | 5.5 | 7.4 | 34.6 | 421 | 1.5, -1.2 | farms | +1 % |
| farms: running | 28.3 | 37.9 | 39.0 | 9.9 | 5.4 | 7.2 | 34.2 | 849 | 1.6, -1.1 (105 m run) | farms | +1 % |
| savannahs | 31.8 | 33.2 | 33.8 | 7.6 | 5.1 | 6.2 | 30.3 | 477 | -6.8, -17.3 | savannahs | -3 % |
| savannahs: running | 31.3 | 34.4 | 36.4 | 7.7 | 4.9 | 6.0 | 30.8 | 940 | -6.6, -17.3 (105 m run) | savannahs | -3 % |
| hills | 29.7 | 35.6 | 36.5 | 8.1 | 4.8 | 6.2 | 32.6 | 447 | -9.7, 5.3 | hills | +1 % |
| hills: running | 31.0 | 35.3 | 36.3 | 8.2 | 5.1 | 6.1 | 31.2 | 931 | -9.7, 5.3 (25 m run) | hills | -3 % |
| mountains | 35.1 | 30.1 | 30.8 | 4.4 | 4.3 | 4.8 | 27.2 | 528 | 10.5, 0.4 | mountains | -1 % |
| mountains: running | 32.9 | 32.9 | 34.0 | 4.4 | 4.7 | 4.9 | 29.3 | 986 | 10.5, 0.5 (104 m run) | mountains | -1 % |
| tundras | 26.5 | 39.9 | 40.8 | 17.1 | 5.6 | 9.8 | 36.2 | 398 | 59.3, -10.2 | tundras | -4 % |
| tundras: running | 26.5 | 40.4 | 43.4 | 18.2 | 5.9 | 10.4 | 36.2 | 795 | 59.4, -10.2 (106 m run) | tundras | -3 % |
| plains | 28.5 | 37.3 | 38.5 | 13.6 | 5.9 | 9.3 | 34.0 | 428 | 0.7, -8.0 | plains | -0 % |
| plains: running | 28.4 | 37.3 | 38.0 | 13.2 | 5.8 | 8.5 | 34.1 | 852 | 0.8, -8.0 (106 m run) | plains | -0 % |
| pine forests | 28.0 | 37.9 | 38.8 | 9.5 | 5.4 | 6.5 | 34.5 | 420 | 31.2, -16.9 | pine forests | -2 % |
| pine forests: running | 27.7 | 39.4 | 40.7 | 9.7 | 5.5 | 6.6 | 34.9 | 831 | 31.3, -17.0 (105 m run) | pine forests | -2 % |
| temperate autumn forests | 21.6 | 55.6 | 56.7 | 10.6 | 5.5 | 6.8 | 45.1 | 324 | 13.3, -38.6 | temperate autumn forests | +21 % |
| temperate autumn forests: running | 22.1 | 55.3 | 57.8 | 11.3 | 5.5 | 6.6 | 43.9 | 664 | 13.3, -38.6 (105 m run) | temperate autumn forests | +25 % |
| marshes | 27.6 | 38.3 | 38.9 | 8.1 | 5.2 | 6.9 | 35.0 | 414 | 24.6, 13.0 | marshes | -1 % |
| marshes: running | 27.9 | 38.3 | 39.3 | 8.6 | 5.4 | 6.9 | 34.6 | 839 | 24.7, 13.0 (90 m run) | marshes | -2 % |
| wetlands | 26.2 | 42.4 | 43.6 | 9.1 | 5.4 | 6.6 | 36.9 | 394 | 20.7, 18.4 | wetlands | -6 % |
| wetlands: running | 27.7 | 41.7 | 44.4 | 9.5 | 5.6 | 7.0 | 34.8 | 832 | 20.7, 18.5 (90 m run) | wetlands | +1 % |
| mountains and peaks | 35.4 | 29.9 | 30.8 | 4.2 | 4.5 | 4.9 | 27.1 | 532 | -15.1, -17.9 | mountains and peaks | -4 % |
| mountains and peaks: running | 36.4 | 29.3 | 30.3 | 4.3 | 4.7 | 5.0 | 26.3 | 1091 | -15.1, -17.8 (71 m run) | mountains and peaks | -3 % |
| volcanoes | 17.4 | 61.9 | 64.8 | 25.6 | 10.2 | 14.5 | 25.6 | 300 | 61.6, -55.5 | volcanoes | +26 % |
| volcanoes: running | 16.4 | 69.9 | 76.6 | 27.8 | 11.8 | 14.8 | 26.5 | 491 | 61.5, -55.4 (105 m run) | volcanoes | +13 % |
| coastal regions | 29.2 | 36.6 | 37.2 | 6.4 | 5.0 | 5.5 | 33.0 | 439 | -30.8, -1.3 | coastal regions | +0 % |
| coastal regions: running | 29.7 | 36.1 | 37.6 | 6.4 | 5.0 | 5.5 | 32.5 | 890 | -30.7, -1.2 (105 m run) | coastal regions | +1 % |
| arctic regions | 27.6 | 38.2 | 38.7 | 7.3 | 5.0 | 7.1 | 35.0 | 414 | 84.0, 19.0 | arctic regions | -1 % |
| arctic regions: running | 27.2 | 38.9 | 39.8 | 7.4 | 4.8 | 7.1 | 35.5 | 817 | 83.9, 19.1 (106 m run) | arctic regions | -1 % |
| canyons | 31.2 | 33.7 | 34.7 | 12.1 | 5.6 | 8.1 | 30.8 | 469 | -8.0, -8.7 | canyons | +1 % |
| canyons: running | 31.5 | 34.0 | 34.7 | 12.2 | 5.8 | 7.8 | 30.6 | 946 | -8.1, -8.8 (106 m run) | canyons | -1 % |
| mesas | 31.9 | 33.2 | 34.5 | 11.5 | 5.9 | 7.8 | 30.2 | 478 | -16.4, 4.6 | mesas | -0 % |
| mesas: running | 31.3 | 34.4 | 35.7 | 12.2 | 5.9 | 7.9 | 30.6 | 940 | -16.3, 4.6 (104 m run) | mesas | -0 % |
| canyon networks | 39.4 | 26.6 | 27.4 | 9.3 | 5.0 | 6.4 | 24.1 | 591 | -13.0, -2.9 | canyon networks | +0 % |
| canyon networks: running | skipped: not measured: she was moved 13323 m in a frame | | | | | | | | | | |
| cold steppes | 30.9 | 33.8 | 34.7 | 8.7 | 5.0 | 7.4 | 31.2 | 463 | 39.8, 34.8 | cold steppes | -0 % |
| cold steppes: running | 29.3 | 36.4 | 37.7 | 9.0 | 5.4 | 7.4 | 32.9 | 881 | 39.9, 34.7 (106 m run) | cold steppes | +2 % |
| highland moorland | 31.6 | 33.4 | 34.0 | 10.7 | 5.7 | 8.9 | 30.5 | 475 | 26.6, 19.2 | highland moorland | -2 % |
| highland moorland: running | 31.2 | 34.4 | 38.7 | 11.5 | 6.0 | 8.9 | 30.8 | 936 | 26.7, 19.3 (105 m run) | highland moorland | -3 % |
| boreal pine forest | 27.2 | 38.6 | 39.4 | 11.4 | 5.8 | 7.3 | 35.6 | 408 | 52.6, -23.5 | boreal pine forest | -1 % |
| boreal pine forest: running | 26.3 | 40.4 | 41.4 | 11.3 | 5.7 | 7.0 | 36.9 | 788 | 52.5, -23.5 (105 m run) | boreal pine forest | -1 % |
| temperate aspen | 29.9 | 36.0 | 36.8 | 9.2 | 5.5 | 6.6 | 32.2 | 450 | 31.2, -10.3 | temperate aspen | +1 % |
| temperate aspen: running | 29.6 | 36.7 | 38.1 | 9.0 | 5.5 | 6.4 | 32.6 | 889 | 31.3, -10.2 (106 m run) | temperate aspen | -1 % |
| volcanic tundra | 28.1 | 37.7 | 39.2 | 16.8 | 5.9 | 9.5 | 34.1 | 422 | 61.5, -0.8 | volcanic tundra | -0 % |
| volcanic tundra: running | 28.1 | 37.7 | 38.8 | 17.1 | 6.1 | 10.3 | 34.1 | 844 | 61.6, -0.8 (101 m run) | volcanic tundra | -1 % |
| burned plain | 32.5 | 32.4 | 33.4 | 8.4 | 5.1 | 6.7 | 29.6 | 488 | 37.5, 0.0 | burned plain | +5 % |
| burned plain: running | 32.3 | 32.8 | 33.8 | 8.5 | 5.2 | 6.7 | 29.8 | 969 | 37.5, 0.1 (106 m run) | burned plain | +3 % |
| geothermal caldera | 28.8 | 36.5 | 37.3 | 9.0 | 5.4 | 6.6 | 33.6 | 432 | 27.8, -43.8 | geothermal caldera | -1 % |
| geothermal caldera: running | 27.6 | 39.6 | 40.6 | 9.8 | 5.8 | 6.9 | 35.0 | 828 | 27.9, -43.8 (105 m run) | geothermal caldera | -0 % |
| glacial | 24.9 | 44.4 | 45.4 | 17.6 | 6.8 | 8.8 | 38.8 | 374 | 76.3, -35.0 | glacial | -1 % |
| glacial: running | 26.0 | 44.2 | 45.8 | 17.3 | 6.9 | 8.6 | 37.1 | 782 | 76.3, -35.1 (68 m run) | glacial | +0 % |
| taigas | 26.3 | 40.4 | 41.1 | 10.3 | 5.2 | 7.0 | 36.8 | 394 | 67.6, 20.8 | taigas | +2 % |
| taigas: running | 26.1 | 41.2 | 42.3 | 11.1 | 5.5 | 7.6 | 37.1 | 782 | 67.7, 20.9 (105 m run) | taigas | +2 % |
| rocky coastal | 40.0 | 26.8 | 27.5 | 6.9 | 4.5 | 5.8 | 23.8 | 601 | -22.9, -13.1 | rocky coastal | +0 % |
| rocky coastal: running | 38.6 | 28.0 | 29.2 | 6.8 | 4.6 | 5.9 | 24.7 | 1159 | -22.8, -13.1 (105 m run) | rocky coastal | -0 % |
| mistward_castle: first hall | 36.8 | 28.2 | 28.7 | 5.0 | 4.6 | 6.0 | 26.0 | 552 | 0.0, 0.0 | - | -2 % |
| heaven_fortress: first hall | 33.6 | 30.9 | 31.6 | 5.1 | 4.9 | 6.0 | 28.8 | 504 | 0.0, 0.0 | - | -2 % |

## AFTER LIST16 changes

Written 2026-11-25 22:32 from the Shipping package's `-RDPerf` run (`pipeline/perf_mistward.ps1`, `RD/RDList16.cpp`), the editor closed, full screen: each city's square and a street about 100 m off it at noon and at midnight; each biome at its nearest site to Brokenspire at noon, standing, then running 30 s from there; the castle's and Heaven's fortress's first hall. Each standing place settled 20 s after the world round her was built, then measured until 15 s and 300 frames had passed (at most 45 s), clear weather, her HUD hidden, facing the longest clear line from her eyes. FPS is the mean over the frames; p95 and p99 are the 95th and 99th percentile frame times in ms; the thread times are the engine's own (stat unit's game, draw, RHI and GPU) averaged over the frames (0 where the build does not keep them). A biome whose name differs from the one under her feet was measured where the put-down found ground.

### 3840x2160

Measured 2026-11-25 21:38 on NVIDIA GeForce RTX 3060, overall quality level -1 (0 low to 3 epic) (by group: res0 view3 aa3 shadow3 gi3 refl3 pp3 tex3 fx3 foliage3 shading3), screen percentage 0, vertical sync off and no frame cap.

| Place | FPS | p95 ms | p99 ms | Game ms | Draw ms | RHI ms | GPU ms | Frames | Where (km) | Biome there | Change |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Brokenspire: square, noon | 26.3 | 43.2 | 44.5 | 15.5 | 7.2 | 9.7 | 36.7 | 395 | 0.0, -0.1 | farms | +6 % |
| Brokenspire: square, midnight | 32.9 | 31.9 | 32.7 | 14.0 | 6.8 | 8.7 | 29.1 | 494 | 0.0, -0.1 | farms | +3 % |
| Brokenspire: street, noon | 26.3 | 42.9 | 44.2 | 14.3 | 7.2 | 9.1 | 36.7 | 395 | 0.0, -0.2 | farms | +2 % |
| Brokenspire: street, midnight | 33.8 | 31.3 | 32.3 | 13.2 | 6.6 | 8.8 | 28.2 | 508 | 0.0, -0.2 | farms | +2 % |
| Ashenreach: square, noon | 25.4 | 43.7 | 45.3 | 17.6 | 8.3 | 11.6 | 37.9 | 382 | 35.0, -0.1 | burned plain | +2 % |
| Ashenreach: square, midnight | 29.4 | 35.2 | 35.9 | 16.0 | 7.2 | 10.1 | 32.8 | 441 | 35.0, -0.1 | burned plain | +1 % |
| Ashenreach: street, noon | 25.2 | 42.9 | 44.5 | 15.9 | 7.8 | 9.8 | 38.4 | 378 | 35.0, -0.2 | burned plain | +1 % |
| Ashenreach: street, midnight | 27.9 | 37.3 | 38.1 | 14.6 | 6.5 | 9.3 | 34.5 | 419 | 35.0, -0.2 | burned plain | +4 % |
| Graymourne: square, noon | 25.7 | 44.0 | 45.1 | 12.0 | 7.2 | 9.5 | 37.6 | 386 | 99.0, -0.0 | coastal regions | +0 % |
| Graymourne: square, midnight | 29.2 | 35.8 | 36.7 | 10.9 | 6.3 | 8.7 | 32.9 | 439 | 99.0, -0.0 | coastal regions | +1 % |
| Graymourne: street, noon | 27.0 | 41.6 | 43.8 | 11.3 | 6.3 | 8.5 | 35.7 | 406 | 98.9, -0.0 | coastal regions | -3 % |
| Graymourne: street, midnight | 30.1 | 35.0 | 35.8 | 10.3 | 5.9 | 8.4 | 32.0 | 451 | 98.9, -0.0 | coastal regions | -1 % |
| Vel Morrath: square, noon | 24.9 | 45.0 | 46.6 | 17.2 | 8.0 | 12.3 | 38.7 | 374 | 27.5, 37.6 | mountains | -1 % |
| Vel Morrath: square, midnight | 28.0 | 37.7 | 39.0 | 14.7 | 6.7 | 10.4 | 34.3 | 420 | 27.5, 37.6 | mountains | -0 % |
| Vel Morrath: street, noon | 27.4 | 41.1 | 42.3 | 15.2 | 7.4 | 10.8 | 35.1 | 412 | 27.5, 37.7 | mountains | +3 % |
| Vel Morrath: street, midnight | 32.8 | 31.8 | 32.4 | 13.7 | 6.6 | 10.0 | 29.1 | 492 | 27.5, 37.7 | mountains | +3 % |
| Kethrys Spire: square, noon | 24.5 | 45.2 | 46.3 | 19.8 | 8.0 | 10.3 | 39.5 | 367 | 76.3, -35.0 | glacial | +0 % |
| Kethrys Spire: square, midnight | 28.6 | 36.5 | 37.5 | 16.8 | 7.1 | 9.2 | 33.6 | 429 | 76.3, -35.0 | glacial | +3 % |
| Kethrys Spire: street, noon | 27.1 | 41.0 | 42.2 | 18.6 | 7.6 | 9.3 | 35.5 | 407 | 76.3, -35.1 | glacial | -1 % |
| Kethrys Spire: street, midnight | 31.4 | 33.4 | 34.9 | 15.9 | 6.3 | 8.5 | 30.5 | 471 | 76.3, -35.1 | glacial | -2 % |
| Heaven: square, noon | 25.9 | 44.1 | 46.7 | 18.4 | 7.8 | 12.2 | 37.0 | 389 | 57.1, -55.5 | volcanoes | +8 % |
| Heaven: square, midnight | 28.7 | 37.7 | 40.5 | 17.0 | 7.0 | 11.3 | 33.4 | 432 | 57.1, -55.5 | volcanoes | +8 % |
| Heaven: street, noon | 27.9 | 39.5 | 41.8 | 16.4 | 7.2 | 11.5 | 34.4 | 419 | 57.1, -55.6 | volcanoes | +4 % |
| Heaven: street, midnight | 29.4 | 36.4 | 39.1 | 15.5 | 6.5 | 9.7 | 32.7 | 442 | 57.1, -55.6 | volcanoes | -3 % |
| grasslands | 27.6 | 38.1 | 39.2 | 10.4 | 6.1 | 7.7 | 35.0 | 415 | 4.5, -0.4 | grasslands | -1 % |
| grasslands: running | 27.7 | 38.5 | 40.0 | 11.2 | 6.3 | 8.1 | 35.0 | 830 | 4.4, -0.3 (105 m run) | grasslands | -1 % |
| meadows | 27.0 | 39.2 | 40.2 | 10.0 | 5.7 | 6.9 | 35.9 | 405 | 6.4, 5.9 | meadows | -3 % |
| meadows: running | 30.5 | 36.6 | 38.6 | 10.1 | 5.8 | 7.1 | 31.7 | 916 | 6.4, 6.0 (104 m run) | meadows | -2 % |
| farms | 28.4 | 37.5 | 38.6 | 11.2 | 6.0 | 8.3 | 34.1 | 426 | 1.5, -1.2 | farms | +3 % |
| farms: running | 27.9 | 38.3 | 39.5 | 11.3 | 6.3 | 8.2 | 34.6 | 838 | 1.6, -1.1 (105 m run) | farms | +0 % |
| savannahs | 31.3 | 33.8 | 34.8 | 8.3 | 5.8 | 6.7 | 30.7 | 471 | -6.8, -17.3 | savannahs | -5 % |
| savannahs: running | 30.8 | 35.1 | 36.6 | 8.4 | 5.8 | 6.7 | 31.2 | 925 | -6.6, -17.3 (106 m run) | savannahs | -5 % |
| hills | 28.2 | 37.6 | 39.0 | 9.0 | 5.7 | 7.2 | 34.1 | 423 | -9.7, 5.3 | hills | -4 % |
| hills: running | 30.7 | 36.6 | 38.0 | 8.9 | 5.7 | 7.0 | 31.5 | 920 | -9.7, 5.3 (26 m run) | hills | -4 % |
| mountains | 34.5 | 30.9 | 31.6 | 4.6 | 5.1 | 5.4 | 27.7 | 517 | 10.5, 0.4 | mountains | -3 % |
| mountains: running | 32.2 | 33.6 | 34.7 | 4.4 | 5.1 | 5.4 | 29.9 | 968 | 10.5, 0.5 (104 m run) | mountains | -3 % |
| tundras | 26.9 | 39.5 | 40.2 | 17.6 | 6.4 | 10.9 | 35.7 | 404 | 59.3, -10.2 | tundras | -3 % |
| tundras: running | 26.3 | 40.8 | 44.6 | 19.4 | 7.3 | 12.0 | 36.4 | 789 | 59.4, -10.2 (105 m run) | tundras | -3 % |
| plains | 27.1 | 39.1 | 40.0 | 14.8 | 6.6 | 9.6 | 35.8 | 406 | 0.7, -8.0 | plains | -5 % |
| plains: running | 26.8 | 39.5 | 40.5 | 14.8 | 6.6 | 9.1 | 36.1 | 806 | 0.8, -8.0 (106 m run) | plains | -6 % |
| pine forests | 27.5 | 38.5 | 39.4 | 10.3 | 6.0 | 7.3 | 35.1 | 413 | 31.2, -16.9 | pine forests | -4 % |
| pine forests: running | 27.2 | 40.2 | 41.6 | 10.7 | 6.3 | 7.4 | 35.5 | 815 | 31.3, -17.0 (105 m run) | pine forests | -4 % |
| temperate autumn forests | 21.9 | 55.6 | 56.6 | 13.1 | 6.5 | 9.6 | 44.5 | 328 | 13.3, -38.6 | temperate autumn forests | +22 % |
| temperate autumn forests: running | 22.2 | 55.1 | 57.9 | 13.6 | 6.2 | 9.1 | 43.8 | 667 | 13.3, -38.6 (106 m run) | temperate autumn forests | +25 % |
| marshes | 27.2 | 39.0 | 40.4 | 8.3 | 5.8 | 7.3 | 35.5 | 409 | 24.6, 13.0 | marshes | -3 % |
| marshes: running | 27.6 | 38.8 | 39.8 | 8.8 | 6.0 | 7.8 | 35.0 | 829 | 24.7, 13.0 (90 m run) | marshes | -3 % |
| wetlands | 24.7 | 42.8 | 43.7 | 9.7 | 6.0 | 7.6 | 39.1 | 372 | 20.7, 18.4 | wetlands | -11 % |
| wetlands: running | 27.4 | 42.3 | 44.6 | 9.8 | 6.0 | 7.5 | 35.2 | 822 | 20.7, 18.5 (90 m run) | wetlands | -0 % |
| mountains and peaks | 34.8 | 30.6 | 31.4 | 4.2 | 5.1 | 5.3 | 27.6 | 523 | -15.1, -17.9 | mountains and peaks | -5 % |
| mountains and peaks: running | 35.7 | 30.2 | 31.5 | 4.5 | 5.3 | 5.4 | 26.9 | 1071 | -15.1, -17.8 (71 m run) | mountains and peaks | -5 % |
| volcanoes | 16.5 | 66.5 | 70.0 | 27.3 | 14.8 | 16.3 | 26.1 | 300 | 61.6, -55.5 | volcanoes | +20 % |
| volcanoes: running | 16.0 | 68.8 | 75.4 | 28.5 | 13.4 | 16.1 | 26.9 | 480 | 61.5, -55.4 (105 m run) | volcanoes | +10 % |
| coastal regions | 28.8 | 37.1 | 37.8 | 6.5 | 5.7 | 6.2 | 33.5 | 432 | -30.8, -1.3 | coastal regions | -1 % |
| coastal regions: running | 29.2 | 36.8 | 38.4 | 6.5 | 5.5 | 5.9 | 32.9 | 878 | -30.7, -1.2 (106 m run) | coastal regions | -1 % |
| arctic regions | 27.2 | 39.0 | 40.4 | 7.9 | 5.4 | 7.3 | 35.6 | 408 | 84.0, 19.0 | arctic regions | -2 % |
| arctic regions: running | 26.9 | 39.5 | 40.6 | 8.1 | 5.4 | 7.4 | 36.0 | 807 | 83.9, 19.1 (106 m run) | arctic regions | -2 % |
| canyons | 30.7 | 34.7 | 36.0 | 13.7 | 6.4 | 9.3 | 31.4 | 460 | -8.0, -8.7 | canyons | -1 % |
| canyons: running | 31.0 | 34.6 | 35.8 | 13.9 | 6.6 | 9.2 | 31.0 | 932 | -8.1, -8.8 (106 m run) | canyons | -2 % |
| mesas | 31.2 | 33.9 | 35.0 | 12.9 | 6.5 | 8.7 | 30.7 | 469 | -16.4, 4.6 | mesas | -3 % |
| mesas: running | 30.8 | 35.4 | 36.8 | 13.9 | 6.5 | 9.3 | 31.2 | 924 | -16.3, 4.6 (104 m run) | mesas | -2 % |
| canyon networks | 38.9 | 27.3 | 28.1 | 11.0 | 6.1 | 7.7 | 24.4 | 583 | -13.0, -2.9 | canyon networks | -1 % |
| canyon networks: running | skipped: not measured: she was moved 13323 m in a frame | | | | | | | | | | |
| cold steppes | 30.3 | 34.8 | 35.8 | 9.2 | 5.7 | 8.5 | 31.7 | 456 | 39.8, 34.8 | cold steppes | -2 % |
| cold steppes: running | 28.8 | 37.4 | 38.9 | 9.6 | 6.0 | 8.4 | 33.5 | 863 | 39.9, 34.7 (105 m run) | cold steppes | +0 % |
| highland moorland | 30.9 | 34.6 | 35.7 | 11.3 | 6.1 | 9.8 | 31.2 | 464 | 26.6, 19.2 | highland moorland | -4 % |
| highland moorland: running | 30.8 | 34.9 | 35.6 | 12.2 | 6.6 | 10.1 | 31.2 | 926 | 26.7, 19.3 (105 m run) | highland moorland | -4 % |
| boreal pine forest | 26.8 | 39.4 | 40.7 | 11.9 | 6.3 | 7.9 | 36.0 | 402 | 52.6, -23.5 | boreal pine forest | -2 % |
| boreal pine forest: running | 26.0 | 40.6 | 41.9 | 11.8 | 6.3 | 7.6 | 37.2 | 781 | 52.5, -23.5 (105 m run) | boreal pine forest | -3 % |
| temperate aspen | 29.5 | 36.8 | 37.8 | 9.5 | 6.1 | 7.3 | 32.6 | 443 | 31.2, -10.3 | temperate aspen | -1 % |
| temperate aspen: running | 29.3 | 37.3 | 38.5 | 9.4 | 6.0 | 7.0 | 32.9 | 879 | 31.3, -10.2 (105 m run) | temperate aspen | -2 % |
| volcanic tundra | 27.7 | 38.2 | 40.7 | 18.1 | 6.8 | 11.7 | 34.6 | 416 | 61.5, -0.8 | volcanic tundra | -2 % |
| volcanic tundra: running | 27.6 | 38.7 | 40.5 | 18.5 | 7.3 | 12.1 | 34.7 | 829 | 61.6, -0.8 (101 m run) | volcanic tundra | -3 % |
| burned plain | 32.0 | 32.9 | 33.7 | 9.0 | 5.6 | 7.5 | 30.0 | 481 | 37.5, 0.0 | burned plain | +4 % |
| burned plain: running | 31.6 | 33.9 | 35.1 | 9.2 | 5.8 | 7.5 | 30.3 | 950 | 37.5, 0.1 (106 m run) | burned plain | +1 % |
| geothermal caldera | 27.5 | 38.3 | 38.9 | 11.3 | 6.2 | 9.7 | 35.2 | 413 | 27.8, -43.8 | geothermal caldera | -6 % |
| geothermal caldera: running | 26.2 | 41.7 | 43.2 | 11.9 | 6.5 | 9.2 | 36.9 | 785 | 27.9, -43.8 (105 m run) | geothermal caldera | -5 % |
| glacial | 24.8 | 44.7 | 45.8 | 19.3 | 8.3 | 10.1 | 38.9 | 372 | 76.3, -35.0 | glacial | -1 % |
| glacial: running | 25.7 | 44.4 | 46.3 | 19.2 | 8.0 | 9.9 | 37.5 | 770 | 76.3, -35.1 (67 m run) | glacial | -1 % |
| taigas | 25.3 | 42.5 | 43.6 | 11.8 | 6.1 | 8.3 | 38.0 | 380 | 67.6, 20.8 | taigas | -2 % |
| taigas: running | 25.5 | 42.0 | 43.8 | 11.9 | 5.9 | 8.3 | 37.8 | 766 | 67.7, 20.9 (105 m run) | taigas | -0 % |
| rocky coastal | 39.2 | 27.4 | 28.4 | 7.2 | 5.0 | 6.2 | 24.3 | 588 | -22.9, -13.1 | rocky coastal | -2 % |
| rocky coastal: running | 37.2 | 30.2 | 33.4 | 8.1 | 6.1 | 6.9 | 25.5 | 1117 | -22.8, -13.1 (106 m run) | rocky coastal | -4 % |
| mistward_castle: first hall | 34.7 | 31.3 | 33.3 | 6.2 | 7.4 | 8.7 | 27.4 | 520 | 0.0, 0.0 | - | -7 % |
| heaven_fortress: first hall | 36.3 | 28.7 | 29.7 | 3.7 | 4.1 | 5.6 | 26.4 | 545 | 0.0, 0.0 | - | +6 % |

## Closed Structures

Written 2026-11-26 23:45 from the Shipping package's `-RDPerf` run (`pipeline/perf_mistward.ps1 -Structures closed|immersive -WildsOnly`, `RD/RDList16.cpp`), the editor closed, full screen, once in each of the Options page's two modes for buildings ([game-modes.md](game-modes.md)): **Immersive Interiors** (every building built whole in the town) and **Closed Structures** (each building a shell, its furniture laid in a level of its own only while she is inside, its windows pictures). Each city's square and a street about 100 m off it at noon and at midnight, each biome at its nearest site to Brokenspire at noon, standing, then running 30 s from there; the same places in both modes and at both resolutions (replayed from one places file). Each standing place settled 20 s after the world round her was built, then measured until 15 s and 300 frames had passed (at most 45 s), clear weather, her HUD hidden. FPS is the mean over the frames; p95 is the 95th percentile frame time in ms; GPU ms the engine's own GPU time.

### 3840x2160

Measured (Closed Structures 2026-11-26 20:53 and Immersive Interiors 2026-11-26 22:37) on NVIDIA GeForce RTX 3060, overall quality level -1 (0 low to 3 epic) (by group: res0 view3 aa3 shadow3 gi3 refl3 pp3 tex3 fx3 foliage3 shading3), screen percentage 0, vertical sync off and no frame cap.

| Place | Immersive FPS | Closed FPS | Change | Immersive p95 ms | Closed p95 ms | Immersive GPU ms | Closed GPU ms | Where (km) | Biome there |
|---|---|---|---|---|---|---|---|---|---|
| Brokenspire: square, noon | 26.5 | 26.6 | +0 % | 42.3 | 41.8 | 36.4 | 36.2 | 0.0, -0.1 | farms |
| Brokenspire: square, midnight | 32.6 | 33.0 | +1 % | 31.9 | 31.7 | 29.4 | 28.9 | 0.0, -0.1 | farms |
| Brokenspire: street, noon | 27.0 | 26.0 | -4 % | 41.7 | 43.5 | 35.9 | 37.2 | 0.0, -0.2 | farms |
| Brokenspire: street, midnight | 33.3 | 33.1 | -1 % | 31.3 | 31.5 | 28.7 | 28.8 | 0.0, -0.2 | farms |
| Ashenreach: square, noon | 25.8 | 25.8 | +0 % | 43.0 | 42.4 | 37.2 | 37.2 | 35.0, -0.1 | burned plain |
| Ashenreach: square, midnight | 29.5 | 29.4 | -0 % | 35.0 | 35.4 | 32.6 | 32.6 | 35.0, -0.1 | burned plain |
| Ashenreach: street, noon | 26.8 | 26.8 | +0 % | 40.2 | 39.9 | 36.0 | 35.8 | 35.0, -0.2 | burned plain |
| Ashenreach: street, midnight | 29.0 | 29.0 | +0 % | 35.7 | 36.0 | 33.2 | 33.0 | 35.0, -0.2 | burned plain |
| Graymourne: square, noon | 25.8 | 25.8 | +0 % | 43.4 | 43.8 | 37.3 | 37.4 | 99.0, -0.0 | coastal regions |
| Graymourne: square, midnight | 29.1 | 29.3 | +1 % | 35.6 | 35.8 | 32.9 | 32.9 | 99.0, -0.0 | coastal regions |
| Graymourne: street, noon | 27.6 | 27.7 | +0 % | 40.7 | 39.8 | 34.8 | 34.8 | 98.9, -0.0 | coastal regions |
| Graymourne: street, midnight | 31.3 | 31.1 | -1 % | 33.2 | 34.0 | 30.4 | 30.8 | 98.9, -0.0 | coastal regions |
| Vel Morrath: square, noon | 25.7 | 24.9 | -3 % | 43.4 | 44.5 | 37.5 | 38.5 | 27.5, 37.6 | mountains |
| Vel Morrath: square, midnight | 28.4 | 28.4 | +0 % | 36.6 | 36.8 | 33.8 | 33.8 | 27.5, 37.6 | mountains |
| Vel Morrath: street, noon | 26.8 | 33.1 | +24 % | 41.7 | 32.7 | 35.9 | 28.8 | 27.5, 37.7 | mountains |
| Vel Morrath: street, midnight | 32.8 | 33.4 | +2 % | 31.7 | 31.2 | 29.2 | 28.6 | 27.5, 37.7 | mountains |
| Kethrys Spire: square, noon | 24.8 | 25.0 | +1 % | 44.7 | 43.9 | 38.7 | 38.4 | 76.3, -35.0 | glacial |
| Kethrys Spire: square, midnight | 28.8 | 28.5 | -1 % | 35.9 | 36.6 | 33.3 | 33.6 | 76.3, -35.0 | glacial |
| Kethrys Spire: street, noon | 26.9 | 26.0 | -3 % | 41.1 | 42.6 | 35.6 | 37.1 | 76.3, -35.1 | glacial |
| Kethrys Spire: street, midnight | 31.1 | 31.3 | +1 % | 33.4 | 33.6 | 30.7 | 30.6 | 76.3, -35.1 | glacial |
| Heaven: square, noon | 26.3 | 26.6 | +1 % | 43.3 | 43.1 | 36.5 | 36.0 | 57.1, -55.5 | volcanoes |
| Heaven: square, midnight | 34.2 | 29.2 | -15 % | 32.5 | 36.0 | 27.7 | 33.0 | 57.1, -55.5 | volcanoes |
| Heaven: street, noon | 35.7 | 27.9 | -22 % | 31.5 | 39.3 | 25.9 | 34.4 | 57.1, -55.6 | volcanoes |
| Heaven: street, midnight | 36.8 | 24.0 | -35 % | 31.4 | 55.3 | 25.2 | 33.2 | 57.1, -55.6 | volcanoes |
| grasslands | 27.7 | 26.6 | -4 % | 38.9 | 41.1 | 35.1 | 36.2 | 4.5, -0.4 | grasslands |
| grasslands: running | 27.9 | 27.9 | +0 % | 38.1 | 38.3 | 34.8 | 34.7 | 4.4, -0.3 | grasslands |
| meadows | 27.3 | 26.9 | -1 % | 38.8 | 39.6 | 35.4 | 36.0 | 6.4, 5.9 | meadows |
| meadows: running | 30.8 | 30.5 | -1 % | 36.5 | 36.9 | 31.4 | 31.6 | 6.4, 6.0 | meadows |
| farms | 28.8 | 28.8 | +0 % | 37.1 | 36.8 | 33.6 | 33.4 | 1.5, -1.2 | farms |
| farms: running | 28.3 | 28.3 | +0 % | 37.5 | 37.5 | 34.2 | 34.1 | 1.6, -1.1 | farms |
| savannahs | 31.3 | 31.4 | +0 % | 34.1 | 34.0 | 30.6 | 30.6 | -6.8, -17.3 | savannahs |
| savannahs: running | 30.9 | 30.3 | -2 % | 35.1 | 37.0 | 31.1 | 31.7 | -6.6, -17.3 | savannahs |
| hills | 29.5 | 28.7 | -3 % | 35.9 | 37.1 | 32.8 | 33.7 | -9.7, 5.3 | hills |
| hills: running | 30.8 | 30.3 | -2 % | 35.5 | 37.3 | 31.4 | 31.8 | -9.7, 5.3 | hills |
| mountains | 34.8 | 34.4 | -1 % | 30.5 | 31.2 | 27.2 | 27.6 | 10.5, 0.4 | mountains |
| mountains: running | 32.4 | 31.9 | -2 % | 33.6 | 34.2 | 29.7 | 30.1 | 10.5, 0.5 | mountains |
| tundras | 26.9 | 25.2 | -6 % | 39.5 | 44.3 | 35.6 | 37.2 | 59.3, -10.2 | tundras |
| tundras: running | 26.3 | 24.6 | -6 % | 40.4 | 51.6 | 36.2 | 37.5 | 59.4, -10.2 | tundras |
| plains | 27.0 | 28.2 | +4 % | 39.2 | 37.5 | 35.9 | 34.3 | 0.7, -8.0 | plains |
| plains: running | 27.7 | 27.9 | +1 % | 38.4 | 38.0 | 35.0 | 34.6 | 0.8, -8.0 | plains |
| pine forests | 27.7 | 27.8 | +0 % | 38.1 | 37.9 | 34.9 | 34.8 | 31.2, -16.9 | pine forests |
| pine forests: running | 27.5 | 27.4 | -0 % | 39.6 | 39.8 | 35.2 | 35.3 | 31.3, -17.0 | pine forests |
| temperate autumn forests | 22.1 | 22.0 | -0 % | 54.7 | 54.5 | 43.9 | 43.9 | 13.3, -38.6 | temperate autumn forests |
| temperate autumn forests: running | 22.5 | 22.2 | -1 % | 54.7 | 55.4 | 43.1 | 43.7 | 13.3, -38.6 | temperate autumn forests |
| marshes | 27.1 | 27.1 | +0 % | 38.9 | 39.4 | 35.7 | 35.7 | 24.6, 13.0 | marshes |
| marshes: running | 27.5 | 27.0 | -2 % | 38.8 | 39.2 | 35.2 | 35.6 | 24.7, 13.0 | marshes |
| wetlands | 26.0 | 26.2 | +1 % | 42.9 | 42.5 | 37.2 | 36.9 | 20.7, 18.4 | wetlands |
| wetlands: running | 27.6 | 27.4 | -1 % | 41.8 | 42.5 | 34.9 | 35.1 | 20.7, 18.5 | wetlands |
| mountains and peaks | 35.2 | 37.7 | +7 % | 30.3 | 28.1 | 27.1 | 25.2 | -15.1, -17.9 | mountains and peaks |
| mountains and peaks: running | 36.1 | 36.8 | +2 % | 29.7 | 29.4 | 26.3 | 25.8 | -15.1, -17.8 | mountains and peaks |
| volcanoes | 16.5 | 16.1 | -2 % | 66.2 | 69.1 | 25.8 | 25.9 | 61.6, -55.5 | volcanoes |
| volcanoes: running | 16.1 | 15.3 | -5 % | 67.9 | 78.9 | 26.5 | 27.2 | 61.5, -55.4 | volcanoes |
| coastal regions | 28.6 | 28.4 | -1 % | 37.2 | 38.4 | 33.7 | 33.9 | -30.8, -1.3 | coastal regions |
| coastal regions: running | 29.2 | 29.2 | +0 % | 37.1 | 37.1 | 33.0 | 32.9 | -30.7, -1.2 | coastal regions |
| arctic regions | 27.1 | 27.1 | +0 % | 38.9 | 39.5 | 35.7 | 35.7 | 84.0, 19.0 | arctic regions |
| arctic regions: running | 26.8 | 26.6 | -1 % | 39.2 | 39.9 | 36.1 | 36.4 | 83.9, 19.1 | arctic regions |
| canyons | 30.9 | 30.6 | -1 % | 34.5 | 34.9 | 31.1 | 31.4 | -8.0, -8.7 | canyons |
| canyons: running | 31.2 | 31.0 | -1 % | 34.4 | 34.7 | 30.8 | 31.0 | -8.1, -8.8 | canyons |
| mesas | 31.2 | 31.2 | +0 % | 34.1 | 34.0 | 30.7 | 30.7 | -16.4, 4.6 | mesas |
| mesas: running | 30.7 | 30.7 | +0 % | 35.2 | 35.3 | 31.2 | 31.2 | -16.3, 4.6 | mesas |
| canyon networks | 39.3 | 38.8 | -1 % | 26.9 | 27.0 | 24.0 | 24.5 | -13.0, -2.9 | canyon networks |
| canyon networks: running | skipped in both modes: not measured: she was moved 13323 m in a frame | | | | | | | | |
| cold steppes | 30.4 | 29.9 | -2 % | 34.7 | 35.5 | 31.6 | 32.1 | 39.8, 34.8 | cold steppes |
| cold steppes: running | 28.7 | 28.7 | +0 % | 37.3 | 37.3 | 33.5 | 33.5 | 39.9, 34.7 | cold steppes |
| highland moorland | 31.3 | 31.0 | -1 % | 34.0 | 34.3 | 30.8 | 30.9 | 26.6, 19.2 | highland moorland |
| highland moorland: running | 31.0 | 30.7 | -1 % | 34.5 | 34.9 | 31.1 | 31.3 | 26.7, 19.3 | highland moorland |
| boreal pine forest | 27.0 | 26.7 | -1 % | 38.9 | 39.9 | 35.7 | 36.2 | 52.6, -23.5 | boreal pine forest |
| boreal pine forest: running | 26.1 | 25.9 | -1 % | 40.5 | 41.2 | 37.0 | 37.3 | 52.5, -23.5 | boreal pine forest |
| temperate aspen | 29.6 | 29.2 | -1 % | 36.5 | 37.3 | 32.7 | 33.0 | 31.2, -10.3 | temperate aspen |
| temperate aspen: running | 29.3 | 29.0 | -1 % | 37.3 | 38.3 | 33.0 | 33.3 | 31.3, -10.2 | temperate aspen |
| volcanic tundra | 27.5 | 27.4 | -0 % | 38.3 | 38.9 | 34.8 | 34.9 | 61.5, -0.8 | volcanic tundra |
| volcanic tundra: running | 27.6 | 27.5 | -0 % | 38.5 | 39.2 | 34.7 | 34.8 | 61.6, -0.8 | volcanic tundra |
| burned plain | 31.8 | 32.2 | +1 % | 33.4 | 32.8 | 30.2 | 29.8 | 37.5, 0.0 | burned plain |
| burned plain: running | 31.6 | 31.9 | +1 % | 33.8 | 33.1 | 30.3 | 30.1 | 37.5, 0.1 | burned plain |
| geothermal caldera | 27.4 | 27.6 | +1 % | 38.2 | 38.2 | 35.1 | 35.0 | 27.8, -43.8 | geothermal caldera |
| geothermal caldera: running | 26.2 | 26.3 | +0 % | 41.6 | 41.6 | 36.8 | 36.8 | 27.9, -43.8 | geothermal caldera |
| glacial | 24.9 | 24.2 | -3 % | 44.6 | 45.5 | 38.7 | 39.8 | 76.3, -35.0 | glacial |
| glacial: running | 27.5 | 27.4 | -0 % | 42.6 | 42.8 | 34.9 | 34.9 | 76.3, -35.1 | glacial |
| taigas | 26.2 | 25.9 | -1 % | 40.3 | 40.9 | 37.0 | 37.4 | 67.6, 20.8 | taigas |
| taigas: running | 26.0 | 25.2 | -3 % | 41.1 | 42.5 | 37.2 | 38.0 | 67.7, 20.9 | taigas |
| rocky coastal | 39.6 | 39.1 | -1 % | 27.0 | 27.5 | 24.1 | 24.2 | -22.9, -13.1 | rocky coastal |
| rocky coastal: running | 38.2 | 37.8 | -1 % | 28.2 | 28.7 | 24.9 | 25.2 | -22.8, -13.1 | rocky coastal |

Over the 81 places measured in both modes: Immersive Interiors 29.0 FPS on average, Closed Structures 28.6 (-1 %). In the cities' squares and streets alone: 29.3 against 28.4 (-3 %).

### 1920x1080

Measured (Closed Structures 2026-11-26 20:01 and Immersive Interiors 2026-11-26 21:45) on NVIDIA GeForce RTX 3060, overall quality level -1 (0 low to 3 epic) (by group: res0 view3 aa3 shadow3 gi3 refl3 pp3 tex3 fx3 foliage3 shading3), screen percentage 0, vertical sync off and no frame cap.

| Place | Immersive FPS | Closed FPS | Change | Immersive p95 ms | Closed p95 ms | Immersive GPU ms | Closed GPU ms | Where (km) | Biome there |
|---|---|---|---|---|---|---|---|---|---|
| Brokenspire: square, noon | 25.4 | 27.2 | +7 % | 43.9 | 42.1 | 37.9 | 35.5 | 0.0, -0.1 | farms |
| Brokenspire: square, midnight | 32.2 | 32.9 | +2 % | 32.8 | 31.8 | 29.5 | 29.0 | 0.0, -0.1 | farms |
| Brokenspire: street, noon | 25.1 | 27.2 | +8 % | 43.9 | 41.5 | 37.9 | 35.5 | 0.0, -0.2 | farms |
| Brokenspire: street, midnight | 32.2 | 33.3 | +3 % | 32.0 | 31.3 | 29.6 | 28.6 | 0.0, -0.2 | farms |
| Ashenreach: square, noon | 23.9 | 25.1 | +5 % | 45.8 | 43.8 | 40.3 | 38.4 | 35.0, -0.1 | burned plain |
| Ashenreach: square, midnight | 27.1 | 28.3 | +4 % | 38.7 | 37.2 | 35.3 | 33.9 | 35.0, -0.1 | burned plain |
| Ashenreach: street, noon | 24.8 | 26.9 | +8 % | 43.0 | 40.1 | 37.7 | 35.8 | 35.0, -0.2 | burned plain |
| Ashenreach: street, midnight | 27.9 | 29.2 | +5 % | 37.5 | 35.6 | 34.5 | 33.0 | 35.0, -0.2 | burned plain |
| Graymourne: square, noon | 25.4 | 26.2 | +3 % | 44.2 | 43.0 | 37.9 | 36.9 | 99.0, -0.0 | coastal regions |
| Graymourne: square, midnight | 28.6 | 30.5 | +7 % | 36.9 | 34.2 | 33.5 | 31.5 | 99.0, -0.0 | coastal regions |
| Graymourne: street, noon | 26.9 | 28.1 | +4 % | 41.3 | 39.5 | 35.7 | 34.2 | 98.9, -0.0 | coastal regions |
| Graymourne: street, midnight | 30.6 | 31.7 | +4 % | 34.7 | 33.3 | 31.1 | 30.3 | 98.9, -0.0 | coastal regions |
| Vel Morrath: square, noon | 26.7 | 26.1 | -2 % | 42.0 | 42.7 | 35.9 | 37.0 | 27.5, 37.6 | mountains |
| Vel Morrath: square, midnight | 27.9 | 28.8 | +3 % | 37.9 | 36.6 | 34.3 | 33.5 | 27.5, 37.6 | mountains |
| Vel Morrath: street, noon | 29.6 | 32.6 | +10 % | 41.3 | 36.8 | 32.3 | 29.3 | 27.5, 37.7 | mountains |
| Vel Morrath: street, midnight | 32.6 | 33.6 | +3 % | 32.0 | 31.3 | 29.4 | 28.5 | 27.5, 37.7 | mountains |
| Kethrys Spire: square, noon | 25.0 | 24.9 | -0 % | 44.3 | 44.0 | 38.4 | 38.7 | 76.3, -35.0 | glacial |
| Kethrys Spire: square, midnight | 28.6 | 28.8 | +1 % | 36.4 | 36.3 | 33.5 | 33.3 | 76.3, -35.0 | glacial |
| Kethrys Spire: street, noon | 26.8 | 27.1 | +1 % | 41.0 | 40.7 | 35.9 | 35.5 | 76.3, -35.1 | glacial |
| Kethrys Spire: street, midnight | 30.9 | 31.4 | +2 % | 33.6 | 33.4 | 30.9 | 30.6 | 76.3, -35.1 | glacial |
| Heaven: square, noon | 25.9 | 26.9 | +4 % | 43.3 | 42.5 | 37.0 | 35.8 | 57.1, -55.5 | volcanoes |
| Heaven: square, midnight | 26.6 | 29.4 | +11 % | 44.6 | 36.0 | 35.7 | 32.7 | 57.1, -55.5 | volcanoes |
| Heaven: street, noon | 27.7 | 31.2 | +13 % | 40.2 | 35.5 | 34.4 | 30.6 | 57.1, -55.6 | volcanoes |
| Heaven: street, midnight | 29.4 | 33.1 | +13 % | 37.5 | 33.1 | 32.7 | 28.8 | 57.1, -55.6 | volcanoes |
| grasslands | 26.7 | 28.6 | +7 % | 39.9 | 36.9 | 36.2 | 33.9 | 4.5, -0.4 | grasslands |
| grasslands: running | 27.4 | 28.9 | +5 % | 39.1 | 36.9 | 35.3 | 33.6 | 4.4, -0.3 | grasslands |
| meadows | 27.1 | 27.7 | +2 % | 39.2 | 38.7 | 35.6 | 34.9 | 6.4, 5.9 | meadows |
| meadows: running | 30.5 | 31.5 | +3 % | 36.9 | 35.8 | 31.6 | 30.7 | 6.4, 6.0 | meadows |
| farms | 28.3 | 29.7 | +5 % | 37.9 | 36.1 | 34.2 | 32.6 | 1.5, -1.2 | farms |
| farms: running | 27.8 | 29.3 | +5 % | 38.6 | 36.4 | 34.8 | 33.0 | 1.6, -1.1 | farms |
| savannahs | 30.9 | 31.3 | +1 % | 34.7 | 33.7 | 31.1 | 30.8 | -6.8, -17.3 | savannahs |
| savannahs: running | 30.4 | 30.9 | +2 % | 35.7 | 35.0 | 31.6 | 31.2 | -6.6, -17.3 | savannahs |
| hills | 28.1 | 30.4 | +8 % | 38.5 | 35.2 | 34.4 | 31.9 | -9.7, 5.3 | hills |
| hills: running | 31.0 | 32.1 | +4 % | 35.6 | 34.3 | 31.2 | 30.1 | -9.7, 5.3 | hills |
| mountains | 33.9 | 36.8 | +9 % | 31.8 | 29.4 | 28.0 | 26.0 | 10.5, 0.4 | mountains |
| mountains: running | 31.9 | 33.5 | +5 % | 34.1 | 32.7 | 30.1 | 28.7 | 10.5, 0.5 | mountains |
| tundras | 26.9 | 26.5 | -1 % | 39.4 | 43.2 | 35.7 | 36.0 | 59.3, -10.2 | tundras |
| tundras: running | 26.2 | 23.1 | -12 % | 40.7 | 55.0 | 36.5 | 37.1 | 59.4, -10.2 | tundras |
| plains | 28.0 | 28.8 | +3 % | 38.0 | 36.9 | 34.5 | 33.5 | 0.7, -8.0 | plains |
| plains: running | 27.8 | 28.7 | +3 % | 38.1 | 36.9 | 34.9 | 33.8 | 0.8, -8.0 | plains |
| pine forests | 27.5 | 27.3 | -1 % | 38.5 | 39.1 | 35.1 | 35.4 | 31.2, -16.9 | pine forests |
| pine forests: running | 27.3 | 27.3 | +0 % | 40.0 | 39.9 | 35.4 | 35.4 | 31.3, -17.0 | pine forests |
| temperate autumn forests | 22.0 | 22.2 | +1 % | 54.5 | 54.0 | 44.3 | 43.8 | 13.3, -38.6 | temperate autumn forests |
| temperate autumn forests: running | 22.3 | 22.3 | +0 % | 54.8 | 54.9 | 43.6 | 43.6 | 13.3, -38.6 | temperate autumn forests |
| marshes | 26.9 | 27.0 | +0 % | 39.3 | 39.4 | 36.0 | 35.9 | 24.6, 13.0 | marshes |
| marshes: running | 27.3 | 27.2 | -0 % | 39.1 | 39.2 | 35.4 | 35.5 | 24.7, 13.0 | marshes |
| wetlands | 26.0 | 26.1 | +0 % | 43.0 | 42.9 | 37.1 | 37.0 | 20.7, 18.4 | wetlands |
| wetlands: running | 27.5 | 27.5 | +0 % | 41.9 | 42.5 | 35.1 | 35.2 | 20.7, 18.5 | wetlands |
| mountains and peaks | 35.0 | 37.7 | +8 % | 30.2 | 28.2 | 27.4 | 25.4 | -15.1, -17.9 | mountains and peaks |
| mountains and peaks: running | 35.8 | 37.0 | +3 % | 29.8 | 29.2 | 26.8 | 25.9 | -15.1, -17.8 | mountains and peaks |
| volcanoes | 16.6 | 15.7 | -5 % | 63.8 | 70.5 | 25.9 | 26.1 | 61.6, -55.5 | volcanoes |
| volcanoes: running | 15.9 | 15.1 | -5 % | 69.7 | 73.8 | 26.6 | 26.9 | 61.5, -55.4 | volcanoes |
| coastal regions | 28.5 | 28.5 | +0 % | 37.4 | 37.4 | 33.8 | 33.9 | -30.8, -1.3 | coastal regions |
| coastal regions: running | 29.0 | 29.0 | +0 % | 37.3 | 37.1 | 33.2 | 33.2 | -30.7, -1.2 | coastal regions |
| arctic regions | 27.0 | 27.1 | +0 % | 38.9 | 39.0 | 35.9 | 35.8 | 84.0, 19.0 | arctic regions |
| arctic regions: running | 26.7 | 26.7 | +0 % | 39.4 | 39.6 | 36.3 | 36.3 | 83.9, 19.1 | arctic regions |
| canyons | 30.7 | 31.8 | +4 % | 34.6 | 33.7 | 31.3 | 30.2 | -8.0, -8.7 | canyons |
| canyons: running | 31.0 | 31.8 | +3 % | 34.6 | 34.1 | 31.0 | 30.2 | -8.1, -8.8 | canyons |
| mesas | 31.1 | 31.2 | +0 % | 33.8 | 33.8 | 30.8 | 30.8 | -16.4, 4.6 | mesas |
| mesas: running | 30.5 | 30.2 | -1 % | 35.3 | 35.5 | 31.4 | 31.7 | -16.3, 4.6 | mesas |
| canyon networks | 38.7 | 38.5 | -1 % | 27.3 | 27.4 | 24.5 | 24.7 | -13.0, -2.9 | canyon networks |
| canyon networks: running | skipped in both modes: not measured: she was moved 13323 m in a frame | | | | | | | | |
| cold steppes | 30.2 | 30.2 | +0 % | 34.6 | 34.8 | 31.8 | 31.9 | 39.8, 34.8 | cold steppes |
| cold steppes: running | 28.5 | 28.5 | +0 % | 37.6 | 37.7 | 33.7 | 33.8 | 39.9, 34.7 | cold steppes |
| highland moorland | 31.1 | 31.1 | +0 % | 34.0 | 34.3 | 30.9 | 30.9 | 26.6, 19.2 | highland moorland |
| highland moorland: running | 30.8 | 30.8 | +0 % | 34.8 | 34.6 | 31.2 | 31.2 | 26.7, 19.3 | highland moorland |
| boreal pine forest | 26.8 | 26.9 | +0 % | 39.0 | 39.2 | 36.1 | 35.9 | 52.6, -23.5 | boreal pine forest |
| boreal pine forest: running | 25.9 | 26.1 | +1 % | 40.9 | 40.5 | 37.3 | 37.1 | 52.5, -23.5 | boreal pine forest |
| temperate aspen | 29.3 | 29.3 | +0 % | 37.2 | 36.8 | 32.9 | 32.8 | 31.2, -10.3 | temperate aspen |
| temperate aspen: running | 29.1 | 29.1 | +0 % | 37.4 | 37.3 | 33.2 | 33.1 | 31.3, -10.2 | temperate aspen |
| volcanic tundra | 27.3 | 27.3 | +0 % | 38.7 | 39.3 | 35.1 | 35.2 | 61.5, -0.8 | volcanic tundra |
| volcanic tundra: running | 27.5 | 27.5 | +0 % | 38.5 | 38.9 | 34.9 | 34.9 | 61.6, -0.8 | volcanic tundra |
| burned plain | 31.6 | 32.2 | +2 % | 33.1 | 32.6 | 30.3 | 29.9 | 37.5, 0.0 | burned plain |
| burned plain: running | 31.4 | 31.6 | +1 % | 34.0 | 33.9 | 30.5 | 30.4 | 37.5, 0.1 | burned plain |
| geothermal caldera | 27.3 | 27.5 | +1 % | 38.4 | 38.4 | 35.4 | 35.1 | 27.8, -43.8 | geothermal caldera |
| geothermal caldera: running | 26.0 | 26.1 | +0 % | 41.8 | 42.0 | 37.1 | 37.0 | 27.9, -43.8 | geothermal caldera |
| glacial | 24.3 | 24.4 | +0 % | 45.1 | 45.0 | 39.4 | 39.4 | 76.3, -35.0 | glacial |
| glacial: running | 27.2 | 27.7 | +2 % | 43.4 | 42.8 | 35.2 | 34.6 | 76.3, -35.1 | glacial |
| taigas | 26.1 | 25.6 | -2 % | 40.7 | 41.5 | 37.0 | 37.7 | 67.6, 20.8 | taigas |
| taigas: running | 25.8 | 25.6 | -1 % | 41.6 | 41.6 | 37.4 | 37.7 | 67.7, 20.9 | taigas |
| rocky coastal | 39.2 | 38.9 | -1 % | 27.4 | 27.8 | 24.3 | 24.5 | -22.9, -13.1 | rocky coastal |
| rocky coastal: running | 37.9 | 37.8 | -0 % | 28.6 | 28.9 | 25.2 | 25.3 | -22.8, -13.1 | rocky coastal |

Over the 81 places measured in both modes: Immersive Interiors 28.4 FPS on average, Closed Structures 29.0 (+2 %). In the cities' squares and streets alone: 27.8 against 29.2 (+5 %).

