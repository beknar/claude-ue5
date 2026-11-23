# Performance

The packaged game's frame rate in every city and every biome, measured before and after the list of 2026-11-22 ([improvements16.txt](improvements16.txt)).

Notes on reading the tables:

- **Fixed seeds:** the runs use the world's and Brokenspire's seeds fixed for a measuring run (16016), and the later runs replay BEFORE's places exactly (`-RDPerfPlaces`), so each row is the same place, hour and view in every section.
- **Two resolutions, one picture:** the 3840 x 2160 and 1920 x 1080 runs read nearly the same, because the engine's default screen percentage (`r.ScreenPercentage` 0: chosen by the display's resolution) renders a 4K screen at about half its width and height. Both draw about 1920 x 1080 before the upscale.
- **Quality level -1** means the game's settings mix levels (no single overall level).
- **The glacial biome** found no dry ground to stand on at its nearest site: it is skipped, and in BEFORE its "running" row was measured from the place before it (the geothermal caldera's, as its "Biome there" says). From MID on, a skipped biome's run is skipped too.
- **BEFORE's canyon networks running row** ran 13 km: she was put back at Brokenspire during it (read it as the run's frames, not a run across the canyons).
- **The worst places before the changes:** the temperate autumn forests (17 FPS, the GPU 54 ms a frame) and the volcanoes (15 FPS, the game thread 30 ms a frame); the cities read 22 to 31 FPS, the GPU 29 to 41 ms a frame.

## BEFORE LIST16 changes

Written 2026-11-22 17:20 from the Shipping package's `-RDPerf` run (`pipeline/perf_mistward.ps1`, `RD/RDList16.cpp`), the editor closed, full screen: each city's square and a street about 100 m off it at noon and at midnight; each biome at its nearest site to Brokenspire at noon, standing, then running 30 s from there; the castle's and Heaven's fortress's first hall. Each standing place settled 20 s after the world round her was built, then measured until 15 s and 300 frames had passed (at most 45 s), clear weather, her HUD hidden, facing the longest clear line from her eyes. FPS is the mean over the frames; p95 and p99 are the 95th and 99th percentile frame times in ms; the thread times are the engine's own (stat unit's game, draw, RHI and GPU) averaged over the frames (0 where the build does not keep them). A biome whose name differs from the one under her feet was measured where the put-down found ground.

### 3840x2160

Measured 2026-11-22 15:35 on NVIDIA GeForce RTX 3060, overall quality level -1 (0 low to 3 epic), screen percentage 0.

| Place | FPS | p95 ms | p99 ms | Game ms | Draw ms | RHI ms | GPU ms | Frames | Where (km) | Biome there |
|---|---|---|---|---|---|---|---|---|---|---|
| Brokenspire: square, noon | 24.5 | 43.5 | 44.5 | 18.4 | 7.4 | 8.9 | 36.6 | 367 | 0.0, -0.1 | farms |
| Brokenspire: square, midnight | 29.7 | 32.7 | 33.3 | 15.7 | 6.4 | 7.7 | 30.2 | 446 | 0.0, -0.1 | farms |
| Brokenspire: street, noon | 25.3 | 42.2 | 43.3 | 18.5 | 7.5 | 8.8 | 35.3 | 380 | 0.0, -0.2 | farms |
| Brokenspire: street, midnight | 31.0 | 31.3 | 32.0 | 16.1 | 6.2 | 8.3 | 28.9 | 465 | 0.0, -0.2 | farms |
| Ashenreach: square, noon | 23.3 | 44.8 | 46.3 | 21.4 | 8.4 | 10.9 | 38.5 | 349 | 35.0, -0.1 | burned plain |
| Ashenreach: square, midnight | 27.2 | 35.5 | 35.9 | 18.2 | 6.5 | 9.2 | 33.1 | 409 | 35.0, -0.1 | burned plain |
| Ashenreach: street, noon | 23.0 | 43.8 | 44.6 | 18.6 | 7.5 | 8.6 | 39.4 | 345 | 35.0, -0.2 | burned plain |
| Ashenreach: street, midnight | 24.9 | 38.9 | 40.1 | 17.4 | 6.7 | 8.6 | 36.4 | 374 | 35.0, -0.2 | burned plain |
| Graymourne: square, noon | 24.1 | 44.5 | 45.6 | 15.6 | 7.0 | 9.1 | 37.2 | 361 | 99.0, -0.0 | coastal regions |
| Graymourne: square, midnight | 26.6 | 36.2 | 37.2 | 13.9 | 6.2 | 8.4 | 33.8 | 400 | 99.0, -0.0 | coastal regions |
| Graymourne: street, noon | 25.7 | 41.4 | 42.7 | 14.3 | 6.5 | 7.8 | 35.1 | 387 | 98.9, -0.0 | coastal regions |
| Graymourne: street, midnight | 29.5 | 32.9 | 33.6 | 12.7 | 5.8 | 7.9 | 30.6 | 442 | 98.9, -0.0 | coastal regions |
| Vel Morrath: square, noon | 23.6 | 44.6 | 46.2 | 19.0 | 7.5 | 10.0 | 38.3 | 355 | 27.5, 37.6 | mountains |
| Vel Morrath: square, midnight | 26.0 | 37.3 | 38.3 | 17.1 | 6.5 | 9.5 | 34.8 | 390 | 27.5, 37.6 | mountains |
| Vel Morrath: street, noon | 25.3 | 42.1 | 43.3 | 19.7 | 7.6 | 10.0 | 35.7 | 380 | 27.5, 37.7 | mountains |
| Vel Morrath: street, midnight | 29.8 | 33.0 | 35.7 | 17.8 | 7.2 | 10.2 | 30.0 | 447 | 27.5, 37.7 | mountains |
| Kethrys Spire: square, noon | 22.8 | 45.6 | 46.6 | 22.6 | 8.0 | 9.8 | 39.5 | 343 | 76.3, -35.0 | glacial |
| Kethrys Spire: square, midnight | 26.8 | 36.0 | 37.3 | 19.7 | 7.1 | 8.5 | 33.6 | 403 | 76.3, -35.0 | glacial |
| Kethrys Spire: street, noon | 26.3 | 39.0 | 40.3 | 21.1 | 7.9 | 9.0 | 34.3 | 395 | 76.3, -35.1 | glacial |
| Kethrys Spire: street, midnight | 30.0 | 32.6 | 33.4 | 18.2 | 6.2 | 8.0 | 30.1 | 450 | 76.3, -35.1 | glacial |
| Heaven: square, noon | 22.5 | 50.8 | 61.3 | 22.8 | 8.2 | 12.1 | 40.8 | 338 | 57.1, -55.5 | volcanoes |
| Heaven: square, midnight | 25.1 | 39.5 | 52.8 | 20.8 | 6.8 | 10.1 | 35.8 | 376 | 57.1, -55.5 | volcanoes |
| Heaven: street, noon | 25.2 | 42.4 | 48.6 | 21.7 | 8.2 | 11.2 | 35.5 | 379 | 57.1, -55.6 | volcanoes |
| Heaven: street, midnight | 27.2 | 37.3 | 44.6 | 20.1 | 6.9 | 10.2 | 33.2 | 409 | 57.1, -55.6 | volcanoes |
| grasslands | 26.6 | 36.9 | 37.8 | 11.2 | 5.3 | 6.3 | 34.0 | 400 | 4.5, -0.4 | grasslands |
| grasslands: running | 29.3 | 36.3 | 37.3 | 9.9 | 5.4 | 6.7 | 33.2 | 881 | 4.4, -0.3 (106 m run) | grasslands |
| meadows | 27.1 | 37.0 | 38.0 | 11.4 | 5.3 | 6.1 | 33.3 | 407 | 6.4, 5.9 | meadows |
| meadows: running | 29.1 | 38.1 | 39.2 | 9.3 | 5.4 | 6.3 | 33.4 | 873 | 6.4, 5.9 (27 m run) | meadows |
| farms | 27.5 | 36.5 | 37.3 | 11.9 | 5.4 | 6.7 | 33.0 | 413 | 1.5, -1.2 | farms |
| farms: running | 29.1 | 36.9 | 38.0 | 9.5 | 5.4 | 6.6 | 33.4 | 875 | 1.6, -1.1 (106 m run) | farms |
| savannahs | 30.3 | 32.4 | 33.6 | 10.0 | 5.3 | 5.7 | 29.7 | 456 | -6.8, -17.3 | savannahs |
| savannahs: running | 32.0 | 33.7 | 34.9 | 8.0 | 5.1 | 6.0 | 30.3 | 962 | -6.6, -17.3 (106 m run) | savannahs |
| hills | 28.8 | 34.5 | 35.7 | 10.7 | 5.5 | 6.5 | 31.5 | 432 | -9.7, 5.3 | hills |
| hills: running | 36.4 | 32.5 | 34.1 | 8.1 | 5.0 | 5.9 | 26.6 | 1092 | -9.7, 5.3 (41 m run) | hills |
| mountains | 35.6 | 28.0 | 29.1 | 6.1 | 4.5 | 4.6 | 25.3 | 534 | 10.5, 0.4 | mountains |
| mountains: running | 35.7 | 31.3 | 32.3 | 4.2 | 4.2 | 4.6 | 27.2 | 1071 | 10.5, 0.5 (82 m run) | mountains |
| tundras | 26.2 | 37.7 | 38.7 | 20.8 | 6.7 | 11.7 | 34.2 | 394 | 59.3, -10.2 | tundras |
| tundras: running | 27.3 | 39.7 | 42.9 | 19.9 | 6.7 | 12.3 | 35.2 | 820 | 59.4, -10.2 (106 m run) | tundras |
| plains | 26.6 | 37.3 | 38.4 | 15.4 | 6.0 | 8.0 | 34.2 | 399 | 0.7, -8.0 | plains |
| plains: running | 28.8 | 37.0 | 38.1 | 13.1 | 5.7 | 8.0 | 33.8 | 864 | 0.8, -8.0 (105 m run) | plains |
| pine forests | 26.6 | 37.3 | 38.4 | 12.6 | 5.7 | 6.8 | 33.8 | 400 | 31.2, -16.9 | pine forests |
| pine forests: running | 27.6 | 39.6 | 41.0 | 10.0 | 5.5 | 6.7 | 35.3 | 827 | 31.3, -17.0 (105 m run) | pine forests |
| temperate autumn forests | 17.2 | 64.9 | 66.0 | 14.2 | 6.1 | 6.6 | 53.5 | 300 | 13.3, -38.6 | temperate autumn forests |
| temperate autumn forests: running | 17.9 | 66.2 | 69.3 | 12.8 | 5.7 | 6.9 | 54.9 | 537 | 13.3, -38.6 (105 m run) | temperate autumn forests |
| marshes | 27.3 | 36.3 | 37.4 | 10.3 | 5.4 | 6.7 | 33.2 | 411 | 24.6, 13.0 | marshes |
| marshes: running | 28.9 | 36.8 | 38.0 | 8.3 | 5.2 | 6.7 | 33.7 | 869 | 24.7, 13.0 (90 m run) | marshes |
| wetlands | 26.9 | 38.3 | 39.7 | 11.6 | 5.7 | 6.7 | 33.5 | 405 | 20.7, 18.4 | wetlands |
| wetlands: running | 27.9 | 38.9 | 39.9 | 9.2 | 5.4 | 6.9 | 35.0 | 837 | 20.7, 18.5 (90 m run) | wetlands |
| mountains and peaks | 33.7 | 29.5 | 30.5 | 6.1 | 5.1 | 4.9 | 26.5 | 506 | -15.1, -17.9 | mountains and peaks |
| mountains and peaks: running | 37.3 | 29.2 | 30.4 | 4.3 | 4.7 | 4.8 | 25.9 | 1118 | -15.1, -17.8 (68 m run) | mountains and peaks |
| volcanoes | 15.4 | 66.5 | 70.3 | 30.5 | 12.7 | 15.2 | 24.9 | 300 | 61.6, -55.5 | volcanoes |
| volcanoes: running | 15.9 | 68.6 | 76.1 | 28.4 | 11.6 | 15.5 | 26.0 | 477 | 61.5, -55.4 (105 m run) | volcanoes |
| coastal regions | 27.3 | 36.0 | 36.8 | 9.2 | 5.5 | 5.8 | 32.7 | 410 | -30.8, -1.3 | coastal regions |
| coastal regions: running | 29.8 | 35.8 | 36.8 | 6.3 | 5.0 | 5.5 | 32.5 | 895 | -30.7, -1.2 (105 m run) | coastal regions |
| arctic regions | 25.8 | 38.1 | 38.9 | 9.9 | 5.1 | 7.0 | 35.1 | 388 | 84.0, 19.0 | arctic regions |
| arctic regions: running | 26.8 | 39.5 | 40.1 | 7.4 | 4.7 | 6.8 | 36.4 | 803 | 83.9, 19.1 (105 m run) | arctic regions |
| canyons | 30.3 | 32.6 | 33.6 | 14.2 | 5.8 | 7.5 | 29.8 | 455 | -8.0, -8.7 | canyons |
| canyons: running | 32.1 | 33.2 | 34.5 | 12.3 | 5.4 | 7.3 | 30.3 | 963 | -8.1, -8.8 (105 m run) | canyons |
| mesas | 30.7 | 32.0 | 32.9 | 13.9 | 5.9 | 8.2 | 29.4 | 461 | -16.4, 4.6 | mesas |
| mesas: running | 32.1 | 34.3 | 36.3 | 14.1 | 6.3 | 9.1 | 30.1 | 965 | -16.3, 4.6 (104 m run) | mesas |
| canyon networks | 35.5 | 27.6 | 28.3 | 11.5 | 5.6 | 6.9 | 25.2 | 533 | -13.0, -2.9 | canyon networks |
| canyon networks: running | 30.5 | 44.7 | 54.3 | 15.1 | 6.8 | 7.9 | 30.0 | 916 | -0.0, -0.1 (13311 m run) | farms |
| cold steppes | 29.2 | 33.7 | 34.8 | 11.5 | 5.7 | 8.3 | 31.0 | 438 | 39.8, 34.8 | cold steppes |
| cold steppes: running | 30.6 | 35.0 | 35.9 | 9.1 | 5.4 | 7.6 | 31.8 | 918 | 39.9, 34.7 (105 m run) | cold steppes |
| highland moorland | 28.4 | 34.7 | 35.7 | 13.5 | 6.0 | 8.9 | 31.6 | 427 | 26.6, 19.2 | highland moorland |
| highland moorland: running | 31.0 | 34.7 | 36.2 | 11.9 | 6.2 | 8.8 | 31.4 | 930 | 26.7, 19.3 (105 m run) | highland moorland |
| boreal pine forest | 25.7 | 38.2 | 39.2 | 14.3 | 6.1 | 7.3 | 35.0 | 387 | 52.6, -23.5 | boreal pine forest |
| boreal pine forest: running | 27.0 | 39.5 | 40.4 | 11.1 | 5.5 | 7.0 | 36.1 | 809 | 52.5, -23.5 (105 m run) | boreal pine forest |
| temperate aspen | 29.1 | 34.8 | 35.5 | 11.1 | 5.6 | 6.7 | 30.9 | 437 | 31.2, -10.3 | temperate aspen |
| temperate aspen: running | 30.6 | 35.7 | 37.4 | 8.7 | 5.1 | 6.4 | 31.6 | 919 | 31.3, -10.2 (105 m run) | temperate aspen |
| volcanic tundra | 27.1 | 36.2 | 37.1 | 19.7 | 6.2 | 10.4 | 33.2 | 407 | 61.5, -0.8 | volcanic tundra |
| volcanic tundra: running | 29.3 | 36.2 | 37.4 | 17.5 | 6.1 | 10.8 | 33.0 | 880 | 61.6, -0.8 (101 m run) | volcanic tundra |
| burned plain | 27.3 | 36.1 | 36.9 | 10.8 | 5.2 | 6.1 | 33.2 | 410 | 37.5, 0.0 | burned plain |
| burned plain: running | 30.2 | 35.8 | 36.9 | 8.5 | 5.0 | 6.0 | 32.1 | 906 | 37.5, 0.1 (105 m run) | burned plain |
| geothermal caldera | 26.3 | 37.4 | 37.9 | 11.0 | 5.2 | 6.1 | 34.7 | 395 | 27.8, -43.8 | geothermal caldera |
| geothermal caldera: running | 27.4 | 39.6 | 40.9 | 9.5 | 5.3 | 6.4 | 35.6 | 821 | 27.9, -43.8 (105 m run) | geothermal caldera |
| glacial | skipped: no ground to stand on | | | | | | | | | |
| glacial: running | 28.0 | 37.9 | 38.9 | 9.4 | 5.1 | 6.3 | 34.9 | 840 | 28.0, -43.7 (106 m run) | geothermal caldera |
| taigas | 24.9 | 39.4 | 40.7 | 13.2 | 5.5 | 7.3 | 36.3 | 374 | 67.6, 20.8 | taigas |
| taigas: running | 26.5 | 40.2 | 41.7 | 11.4 | 5.4 | 7.6 | 36.8 | 796 | 67.7, 20.9 (106 m run) | taigas |
| rocky coastal | 36.9 | 27.0 | 27.5 | 8.3 | 4.3 | 5.3 | 24.2 | 554 | -22.9, -13.1 | rocky coastal |
| rocky coastal: running | 39.0 | 27.6 | 28.7 | 6.6 | 4.3 | 5.5 | 24.6 | 1171 | -22.8, -13.1 (106 m run) | rocky coastal |
| mistward_castle: first hall | 34.9 | 27.5 | 28.2 | 6.7 | 4.9 | 5.7 | 25.9 | 523 | 0.0, 0.0 | - |
| heaven_fortress: first hall | 31.7 | 30.3 | 30.9 | 7.2 | 5.2 | 5.7 | 28.3 | 476 | 0.0, 0.0 | - |

### 1920x1080

Measured 2026-11-22 16:27 on NVIDIA GeForce RTX 3060, overall quality level -1 (0 low to 3 epic), screen percentage 0.

| Place | FPS | p95 ms | p99 ms | Game ms | Draw ms | RHI ms | GPU ms | Frames | Where (km) | Biome there |
|---|---|---|---|---|---|---|---|---|---|---|
| Brokenspire: square, noon | 23.9 | 44.8 | 45.5 | 17.7 | 7.2 | 8.8 | 37.7 | 359 | 0.0, -0.1 | farms |
| Brokenspire: square, midnight | 28.1 | 34.6 | 35.1 | 15.8 | 6.4 | 7.4 | 32.1 | 422 | 0.0, -0.1 | farms |
| Brokenspire: street, noon | 25.4 | 42.3 | 44.0 | 18.4 | 7.4 | 8.3 | 35.5 | 382 | 0.0, -0.2 | farms |
| Brokenspire: street, midnight | 29.6 | 33.0 | 33.8 | 15.6 | 6.5 | 7.8 | 30.4 | 445 | 0.0, -0.2 | farms |
| Ashenreach: square, noon | 23.9 | 44.1 | 46.2 | 22.2 | 9.3 | 11.0 | 37.8 | 359 | 35.0, -0.1 | burned plain |
| Ashenreach: square, midnight | 27.1 | 35.8 | 36.2 | 17.9 | 6.9 | 8.9 | 33.3 | 407 | 35.0, -0.1 | burned plain |
| Ashenreach: street, noon | 23.1 | 44.0 | 44.8 | 18.5 | 7.7 | 9.1 | 39.2 | 347 | 35.0, -0.2 | burned plain |
| Ashenreach: street, midnight | 24.9 | 39.0 | 39.8 | 16.9 | 6.4 | 8.2 | 36.3 | 374 | 35.0, -0.2 | burned plain |
| Graymourne: square, noon | 24.5 | 44.0 | 44.9 | 15.6 | 7.0 | 8.7 | 37.1 | 368 | 99.0, -0.0 | coastal regions |
| Graymourne: square, midnight | 26.6 | 36.3 | 37.3 | 13.7 | 6.2 | 8.0 | 33.9 | 399 | 99.0, -0.0 | coastal regions |
| Graymourne: street, noon | 26.4 | 40.5 | 42.1 | 14.3 | 6.7 | 7.9 | 34.1 | 397 | 98.9, -0.0 | coastal regions |
| Graymourne: street, midnight | 29.4 | 33.2 | 33.9 | 13.0 | 6.1 | 7.9 | 30.6 | 441 | 98.9, -0.0 | coastal regions |
| Vel Morrath: square, noon | 24.0 | 44.0 | 45.4 | 18.9 | 7.8 | 10.3 | 37.6 | 361 | 27.5, 37.6 | mountains |
| Vel Morrath: square, midnight | 25.8 | 37.6 | 38.6 | 16.8 | 6.7 | 9.2 | 35.1 | 387 | 27.5, 37.6 | mountains |
| Vel Morrath: street, noon | 25.2 | 42.1 | 43.3 | 19.5 | 7.9 | 10.4 | 35.5 | 379 | 27.5, 37.7 | mountains |
| Vel Morrath: street, midnight | 29.8 | 33.3 | 34.9 | 17.4 | 7.2 | 9.8 | 30.1 | 448 | 27.5, 37.7 | mountains |
| Kethrys Spire: square, noon | 22.8 | 45.6 | 47.2 | 22.5 | 8.0 | 9.5 | 39.5 | 342 | 76.3, -35.0 | glacial |
| Kethrys Spire: square, midnight | 26.8 | 36.0 | 36.7 | 19.7 | 7.2 | 8.4 | 33.5 | 403 | 76.3, -35.0 | glacial |
| Kethrys Spire: street, noon | 26.4 | 39.2 | 40.4 | 20.3 | 7.5 | 8.4 | 34.2 | 396 | 76.3, -35.1 | glacial |
| Kethrys Spire: street, midnight | 29.9 | 32.8 | 33.4 | 17.9 | 6.4 | 8.0 | 30.2 | 449 | 76.3, -35.1 | glacial |
| Heaven: square, noon | 22.4 | 51.7 | 61.4 | 22.1 | 8.1 | 11.2 | 41.0 | 337 | 57.1, -55.5 | volcanoes |
| Heaven: square, midnight | 23.9 | 45.3 | 56.5 | 23.7 | 9.2 | 13.1 | 37.6 | 359 | 57.1, -55.5 | volcanoes |
| Heaven: street, noon | 25.5 | 42.4 | 46.0 | 24.3 | 10.7 | 12.6 | 35.1 | 383 | 57.1, -55.6 | volcanoes |
| Heaven: street, midnight | 26.7 | 39.5 | 46.4 | 22.2 | 8.9 | 12.2 | 33.6 | 401 | 57.1, -55.6 | volcanoes |
| grasslands | 26.4 | 37.5 | 39.3 | 12.6 | 6.3 | 7.5 | 34.2 | 396 | 4.5, -0.4 | grasslands |
| grasslands: running | 29.1 | 36.6 | 37.7 | 9.9 | 5.3 | 6.8 | 33.6 | 873 | 4.4, -0.3 (106 m run) | grasslands |
| meadows | 26.9 | 37.5 | 38.6 | 11.6 | 5.6 | 6.4 | 33.5 | 404 | 6.4, 5.9 | meadows |
| meadows: running | 28.9 | 38.4 | 40.0 | 9.6 | 5.9 | 6.5 | 33.5 | 868 | 6.4, 5.9 (27 m run) | meadows |
| farms | 27.0 | 36.9 | 37.8 | 12.3 | 5.7 | 7.2 | 33.5 | 406 | 1.5, -1.2 | farms |
| farms: running | 28.9 | 37.2 | 38.3 | 9.8 | 5.4 | 6.9 | 33.6 | 869 | 1.6, -1.1 (106 m run) | farms |
| savannahs | 30.0 | 33.0 | 33.9 | 9.8 | 5.3 | 5.8 | 30.1 | 450 | -6.8, -17.3 | savannahs |
| savannahs: running | 31.6 | 34.1 | 35.5 | 7.9 | 5.2 | 5.7 | 30.7 | 948 | -6.6, -17.3 (105 m run) | savannahs |
| hills | 28.7 | 34.8 | 35.5 | 10.3 | 5.3 | 6.2 | 31.6 | 431 | -9.7, 5.3 | hills |
| hills: running | 36.4 | 32.5 | 34.6 | 8.0 | 5.0 | 5.9 | 26.6 | 1094 | -9.7, 5.3 (41 m run) | hills |
| mountains | 35.4 | 28.1 | 29.1 | 5.9 | 4.6 | 4.6 | 25.3 | 532 | 10.5, 0.4 | mountains |
| mountains: running | 35.8 | 31.0 | 32.4 | 4.1 | 4.2 | 4.6 | 27.1 | 1074 | 10.5, 0.5 (82 m run) | mountains |
| tundras | 25.3 | 38.8 | 39.9 | 19.8 | 6.3 | 9.6 | 35.4 | 379 | 59.3, -10.2 | tundras |
| tundras: running | 26.5 | 40.7 | 42.4 | 19.9 | 7.3 | 11.8 | 36.5 | 794 | 59.4, -10.2 (105 m run) | tundras |
| plains | 26.7 | 36.9 | 37.9 | 15.8 | 6.2 | 8.2 | 34.0 | 401 | 0.7, -8.0 | plains |
| plains: running | 29.4 | 36.1 | 37.1 | 13.3 | 5.8 | 8.2 | 33.2 | 882 | 0.8, -8.0 (105 m run) | plains |
| pine forests | 26.9 | 36.5 | 37.6 | 11.9 | 5.3 | 6.4 | 33.6 | 404 | 31.2, -16.9 | pine forests |
| pine forests: running | 27.7 | 39.2 | 40.7 | 9.7 | 5.3 | 6.5 | 35.1 | 832 | 31.3, -17.0 (106 m run) | pine forests |
| temperate autumn forests | 17.4 | 64.5 | 65.2 | 14.2 | 5.9 | 6.5 | 53.3 | 300 | 13.3, -38.6 | temperate autumn forests |
| temperate autumn forests: running | 18.0 | 65.4 | 69.2 | 12.5 | 5.4 | 6.5 | 54.5 | 541 | 13.3, -38.6 (105 m run) | temperate autumn forests |
| marshes | 27.1 | 36.7 | 37.6 | 10.2 | 5.2 | 6.4 | 33.5 | 408 | 24.6, 13.0 | marshes |
| marshes: running | 28.8 | 37.0 | 38.0 | 8.2 | 5.2 | 6.5 | 33.9 | 864 | 24.7, 13.0 (90 m run) | marshes |
| wetlands | 27.1 | 38.2 | 39.7 | 11.5 | 5.3 | 6.4 | 33.4 | 407 | 20.7, 18.4 | wetlands |
| wetlands: running | 27.5 | 39.2 | 40.7 | 8.9 | 5.1 | 6.3 | 35.4 | 827 | 20.7, 18.5 (90 m run) | wetlands |
| mountains and peaks | 34.0 | 29.4 | 30.0 | 5.9 | 4.8 | 4.7 | 26.4 | 510 | -15.1, -17.9 | mountains and peaks |
| mountains and peaks: running | 37.2 | 28.9 | 29.8 | 4.2 | 4.4 | 4.7 | 25.9 | 1117 | -15.1, -17.8 (68 m run) | mountains and peaks |
| volcanoes | 16.0 | 64.9 | 68.2 | 29.2 | 10.5 | 14.7 | 24.9 | 300 | 61.6, -55.5 | volcanoes |
| volcanoes: running | 16.4 | 69.0 | 76.9 | 27.3 | 10.7 | 14.6 | 25.9 | 491 | 61.5, -55.4 (105 m run) | volcanoes |
| coastal regions | 27.6 | 36.1 | 36.7 | 8.3 | 5.1 | 5.2 | 32.7 | 414 | -30.8, -1.3 | coastal regions |
| coastal regions: running | 29.8 | 35.8 | 36.7 | 6.1 | 4.9 | 5.4 | 32.5 | 895 | -30.7, -1.2 (105 m run) | coastal regions |
| arctic regions | 26.0 | 38.0 | 39.1 | 9.8 | 5.0 | 6.8 | 34.9 | 390 | 84.0, 19.0 | arctic regions |
| arctic regions: running | 26.7 | 39.6 | 40.6 | 7.4 | 4.9 | 6.8 | 36.5 | 801 | 83.9, 19.1 (105 m run) | arctic regions |
| canyons | 30.2 | 32.7 | 33.6 | 14.3 | 5.8 | 7.5 | 29.9 | 454 | -8.0, -8.7 | canyons |
| canyons: running | 32.1 | 33.1 | 34.2 | 12.1 | 5.4 | 6.9 | 30.2 | 964 | -8.1, -8.8 (105 m run) | canyons |
| mesas | 30.6 | 32.2 | 33.0 | 13.9 | 5.9 | 7.6 | 29.5 | 459 | -16.4, 4.6 | mesas |
| mesas: running | 33.0 | 32.7 | 33.8 | 12.3 | 5.6 | 7.6 | 29.4 | 991 | -16.3, 4.6 (104 m run) | mesas |
| canyon networks | 35.5 | 27.4 | 28.2 | 11.2 | 5.0 | 5.9 | 25.2 | 533 | -13.0, -2.9 | canyon networks |
| canyon networks: running | 30.8 | 42.8 | 52.4 | 14.0 | 6.4 | 7.4 | 30.0 | 924 | -0.0, -0.1 (13311 m run) | farms |
| cold steppes | 29.4 | 33.4 | 34.0 | 10.8 | 5.3 | 7.2 | 30.8 | 441 | 39.8, 34.8 | cold steppes |
| cold steppes: running | 31.0 | 34.4 | 35.4 | 8.9 | 5.3 | 7.2 | 31.3 | 930 | 39.9, 34.7 (105 m run) | cold steppes |
| highland moorland | 30.0 | 33.0 | 33.7 | 12.5 | 5.7 | 8.9 | 30.1 | 450 | 26.6, 19.2 | highland moorland |
| highland moorland: running | 32.0 | 33.4 | 34.1 | 11.3 | 5.9 | 8.4 | 30.3 | 961 | 26.7, 19.3 (105 m run) | highland moorland |
| boreal pine forest | 25.8 | 37.9 | 38.7 | 14.3 | 6.0 | 7.4 | 35.0 | 388 | 52.6, -23.5 | boreal pine forest |
| boreal pine forest: running | 26.9 | 39.6 | 40.7 | 11.9 | 5.8 | 7.3 | 36.1 | 808 | 52.5, -23.5 (105 m run) | boreal pine forest |
| temperate aspen | 28.8 | 35.1 | 36.0 | 11.3 | 5.5 | 6.3 | 31.0 | 433 | 31.2, -10.3 | temperate aspen |
| temperate aspen: running | 30.9 | 35.5 | 36.8 | 8.7 | 5.0 | 6.1 | 31.4 | 928 | 31.3, -10.2 (106 m run) | temperate aspen |
| volcanic tundra | 27.2 | 36.1 | 37.4 | 19.9 | 6.8 | 10.5 | 33.0 | 408 | 61.5, -0.8 | volcanic tundra |
| volcanic tundra: running | 29.6 | 36.0 | 38.7 | 16.9 | 5.8 | 9.8 | 32.7 | 890 | 61.6, -0.8 (101 m run) | volcanic tundra |
| burned plain | 27.7 | 35.8 | 36.3 | 10.6 | 5.3 | 6.1 | 32.7 | 416 | 37.5, 0.0 | burned plain |
| burned plain: running | 31.0 | 34.8 | 36.1 | 8.9 | 5.2 | 6.5 | 31.3 | 931 | 37.5, 0.1 (106 m run) | burned plain |
| geothermal caldera | 26.3 | 37.4 | 38.4 | 12.8 | 6.3 | 8.0 | 34.4 | 395 | 27.8, -43.8 | geothermal caldera |
| geothermal caldera: running | 27.5 | 39.4 | 40.7 | 10.5 | 5.6 | 7.7 | 35.5 | 826 | 27.9, -43.8 (105 m run) | geothermal caldera |
| glacial | skipped: no ground to stand on | | | | | | | | | |
| glacial: running | 28.3 | 37.5 | 39.0 | 10.2 | 5.1 | 6.9 | 34.6 | 848 | 28.0, -43.7 (105 m run) | geothermal caldera |
| taigas | 24.6 | 39.8 | 41.5 | 14.8 | 6.6 | 8.9 | 36.4 | 369 | 67.6, 20.8 | taigas |
| taigas: running | 26.4 | 40.7 | 42.3 | 12.9 | 6.0 | 9.0 | 36.7 | 793 | 67.7, 20.9 (105 m run) | taigas |
| rocky coastal | 36.4 | 27.3 | 28.0 | 9.1 | 5.0 | 6.1 | 24.4 | 547 | -22.9, -13.1 | rocky coastal |
| rocky coastal: running | 38.7 | 27.8 | 28.7 | 6.6 | 4.5 | 5.8 | 24.8 | 1161 | -22.8, -13.1 (105 m run) | rocky coastal |
| mistward_castle: first hall | 34.9 | 27.6 | 28.1 | 6.8 | 4.9 | 5.5 | 25.9 | 524 | 0.0, 0.0 | - |
| heaven_fortress: first hall | 31.8 | 30.4 | 31.0 | 7.1 | 5.2 | 5.7 | 28.3 | 477 | 0.0, 0.0 | - |

