# random_dungeoncombat_level sound self test: starts the level as a game of its own (off screen, the real-time audio
# device; the editor may stay open) with -RDSoundTest=<dir>. The generator then records what the audio device puts out
# while it plays one flat sound and the same placed sound at known places round her (2 m ahead, 4 m right, 4 m left,
# 12 m and 25 m ahead), writes <dir>\soundtest.wav and soundtest.txt, and quits. pipeline\blender_numpy\rdc_sound_check.py
# then reads the recording: is a placed sound there, on the right side, quieter with distance?
# Args: [out_dir] [python with numpy]      e.g.  .\799_rdc_sound_test.ps1 C:\temp\rdc_sound
param([string]$Out = (Join-Path $env:TEMP "rdc_sound_test"), [string]$Py = "python")
$ue = "E:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe"
$proj = Join-Path $PSScriptRoot "..\..\claude_ue5\claude_ue5.uproject" | Resolve-Path
New-Item -ItemType Directory -Force $Out | Out-Null
Remove-Item (Join-Path $Out "soundtest.*") -ErrorAction SilentlyContinue -Confirm:$false
# (a game without the focus is silent by default: the test turns that off for itself)
$a = @("`"$proj`"", "/Game/RandomDungeon/Maps/random_dungeoncombat_level", "-game", "-RenderOffScreen", "-ResX=640", "-ResY=360", "-unattended", "-nosplash", "-RDSoundTest=`"$Out`"")
$p = Start-Process -FilePath $ue -ArgumentList $a -PassThru
if (-not $p.WaitForExit(300000)) { $p.Kill(); "the game did not quit within 5 minutes"; exit 1 }
if (-not (Test-Path (Join-Path $Out "soundtest.wav"))) { "no recording in $Out (see claude_ue5\Saved\Logs)"; exit 1 }
& $Py (Join-Path $PSScriptRoot "..\blender_numpy\rdc_sound_check.py") $Out
