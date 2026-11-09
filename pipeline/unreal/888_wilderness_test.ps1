# The wilderness test (888_wilderness_test.py) on brokenspire: the same driver as 884_brokenspire_test.ps1.
# starts PIE, waits for UEDPIE_0_brokenspire, arms 888_wilderness_test.py with the plan, waits for a NEW "WILDTEST done | <tag>"
# line, stops PIE, sets rd.HeroMenu back to 1 and leaves the editor on brokenspire with play stopped.
# -Light (as 884's, 2026-11-08b: play in the editor's 4K viewport ran the 12 GB GPU out of memory): the editor on an empty level
# (rl_scratch), its viewports not drawn live and virtual shadows off, play in a window of its own (1280 x 720,
# RD/RDEditorPlay.cpp), and the town opened from play (OpenLevel brokenspire?Hero=<Hero>); all put back after.
# Args: plan tag [maxSeconds] [-Light] [-Hero Warrior]   e.g.  .\888_wilderness_test.ps1 "world,towns" s1 -Light   (plan "all": every step)
param([string]$plan, [string]$tag, [int]$maxs = 1800, [switch]$Light, [string]$Hero = "Warrior")
if ($plan -eq "all") { $plan = "world,look,stream,towns,gate,map,places,travel,save" }
$L = "brokenspire"
$py = $env:UE_PY; if (-not $py) { $py = "python" }
$ex = Join-Path $PSScriptRoot "..\blender_numpy\ue_exec.py"
$log = Join-Path $PSScriptRoot "..\..\claude_ue5\Saved\Logs\claude_ue5.log"
$open = "import unreal; les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); print('LEVEL', w.get_name() == '$L' or les.load_level('/Game/RandomDungeon/Maps/$L'))"
$openLight = "import unreal; unreal.EditorLoadingAndSavingUtils.load_map('/Game/RandomLevel/Test/rl_scratch'); [unreal.SystemLibrary.execute_console_command(None, c) for c in ('obj gc', 'r.Shadow.Virtual.Enable 0')]; print('viewports', unreal.RDEditorPlay.set_level_viewports_realtime(False))"
$cvar = "import unreal; unreal.SystemLibrary.execute_console_command(None, 'rd.HeroMenu {0}'); print('rd.HeroMenu', unreal.SystemLibrary.get_console_variable_int_value('rd.HeroMenu'))"
function Restore {
    & $py $ex -c ($cvar -f 1) 2>$null | Out-Null
    & $py $ex -c "import unreal; print('windows shown again', unreal.RDDungeonGenerator.slate_restore_any_view())" 2>$null | Out-Null
    if ($Light) { & $py $ex -c "import unreal; unreal.SystemLibrary.execute_console_command(None, 'r.Shadow.Virtual.Enable 1'); unreal.RDEditorPlay.set_level_viewports_realtime(True)" 2>$null | Out-Null }
}
# (CLAUDE.md: the old objects collected before new work in the editor and after a level is closed: obj gc)
$gc = "import unreal; unreal.SystemLibrary.execute_console_command(None, 'obj gc'); print('obj gc')"
if ($Light) { & $py $ex -c $openLight 2>$null | Out-Null } else { & $py $ex -c $open 2>$null | Out-Null; & $py $ex -c $gc 2>$null | Out-Null }
& $py $ex -c ($cvar -f 0) 2>$null | Out-Null
$pat = "WILDTEST done \| $tag \|"
$n0 = (Select-String -Path $log -Pattern $pat | Measure-Object).Count
$e0 = (Select-String -Path $log -Pattern "WILDTEST error" | Measure-Object).Count
$stop = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()"
$begin = if ($Light) { "import unreal; print('pie requested', unreal.RDEditorPlay.play_in_new_window(1280, 720))" } else { "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); print('pie requested')" }
$isup = "import unreal; g = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); print('PIE', g.get_path_name() if g else None)"
$travel = "import unreal; w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); unreal.GameplayStatics.open_level(w, '$L', True, 'Hero=$Hero'); print('travel')"
& $py $ex -c $begin 2>$null | Out-Null
$up = $false; $travelled = -not $Light
for ($k = 0; $k -lt 60 -and -not $up; $k++) {
    Start-Sleep 5
    $o = & $py $ex -c $isup 2>$null
    if ("$o" -match "UEDPIE_0_$L\.") { $up = $true }
    elseif ($Light -and -not $travelled -and "$o" -match "UEDPIE_0_rl_scratch\.") { & $py $ex -c $travel 2>$null | Out-Null; $travelled = $true }
    elseif ($k % 6 -eq 5 -and "$o" -notmatch "UEDPIE") { & $py $ex -c $begin 2>$null | Out-Null }
}
if (-not $up) { & $py $ex -c $stop 2>$null | Out-Null; Restore; & $py $ex -c $open 2>$null | Out-Null; "PIE did not start on ${L}: $o"; exit 1 }
Start-Sleep 8
$o = & $py $ex (Join-Path $PSScriptRoot "888_wilderness_test.py") $plan $tag 2>$null
if (-not ("$o" -match "wilderness test armed")) { & $py $ex -c $stop | Out-Null; Restore; & $py $ex -c $open 2>$null | Out-Null; "arm failed: $o"; exit 1 }
$t = 0; $line = $null
while ($t -lt $maxs) {
    Start-Sleep 10; $t += 10
    if (-not (Get-Process UnrealEditor -ErrorAction SilentlyContinue)) { "EDITOR GONE"; exit 1 }
    $all = Select-String -Path $log -Pattern $pat
    if (($all | Measure-Object).Count -gt $n0) { $line = ($all | Select-Object -Last 1).Line; break }
    $err = Select-String -Path $log -Pattern "WILDTEST error"
    if (($err | Measure-Object).Count -gt $e0) { $line = ($err | Select-Object -Last 1).Line; break }
}
Start-Sleep 3; & $py $ex -c $stop 2>$null | Out-Null; Start-Sleep 6
Restore
# (the castle step ends play in the castle: the editor is left on the town)
& $py $ex -c $open 2>$null | Out-Null
& $py $ex -c $gc 2>$null | Out-Null
if ($line) { $line.Substring($line.IndexOf("WILDTEST")) } else { "no result after $maxs s"; (Select-String -Path $log -Pattern "WILDTEST " | Select-Object -Last 5).Line }
