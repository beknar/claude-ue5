# Performance

The packaged game's frame rate in every city and every biome, measured before and after the list of 2026-11-22 ([improvements16.txt](improvements16.txt)).

Notes on reading the tables:

- **Fixed seeds:** the runs use the world's and Brokenspire's seeds fixed for a measuring run (16016), and the later runs replay BEFORE's places exactly (`-RDPerfPlaces`), so each row is the same place, hour and view in every section.
- **One resolution:** the runs are at the desktop's own (3840 x 2160). The first BEFORE run also measured 1920 x 1080 and read nearly the same: the engine's default screen percentage (`r.ScreenPercentage` 0, chosen by the display's resolution) renders a 4K screen at about half its width and height, so both draw about 1920 x 1080 before the upscale.
- **Quality:** every group at Epic (3); the overall level reads -1 because the resolution quality is 0 (the screen percentage left to the engine). Vertical sync off and no frame cap, whatever the player's settings hold.
- **The first BEFORE run was measured again** (2026-11-22, 23:37) after PR #111's review fixed the measuring run: the hour now held, the run's turn at most once a second, the picture taken after the measure, a row never filed for another place.
- **A biome with no dry ground at its nearest site** is measured at its next. The glacial biome's next site is by Kethrys Spire.
- **The canyon networks' run is not measured:** she was moved 13 km in a frame during it (put back at Brokenspire), and the run refuses such a row.
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

