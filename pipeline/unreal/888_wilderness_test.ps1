# The wilderness test (888_wilderness_test.py) on brokenspire: the same driver as 884_brokenspire_test.ps1.
# starts PIE, waits for UEDPIE_0_brokenspire, arms 888_wilderness_test.py with the plan, waits for a NEW "WILDTEST done | <tag>"
# line, stops PIE, sets rd.HeroMenu back to 1 and leaves the editor on brokenspire with play stopped.
# Args: plan tag [maxSeconds]   e.g.  .\884_brokenspire_test.ps1 "town,doors,talk" b1     (plan "all": every step, 884's order)
param([string]$plan, [string]$tag, [int]$maxs = 1800)
if ($plan -eq "all") { $plan = "world,look,stream,towns,gate,map,places,travel,save" }
$L = "brokenspire"
$py = $env:UE_PY; if (-not $py) { $py = "python" }
$ex = Join-Path $PSScriptRoot "..\blender_numpy\ue_exec.py"
$log = Join-Path $PSScriptRoot "..\..\claude_ue5\Saved\Logs\claude_ue5.log"
$open = "import unreal; les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); print('LEVEL', w.get_name() == '$L' or les.load_level('/Game/RandomDungeon/Maps/$L'))"
$cvar = "import unreal; unreal.SystemLibrary.execute_console_command(None, 'rd.HeroMenu {0}'); print('rd.HeroMenu', unreal.SystemLibrary.get_console_variable_int_value('rd.HeroMenu'))"
function Restore {
    & $py $ex -c ($cvar -f 1) 2>$null | Out-Null
    & $py $ex -c "import unreal; print('windows shown again', unreal.RDDungeonGenerator.slate_restore_any_view())" 2>$null | Out-Null
}
# (CLAUDE.md: the old objects collected before new work in the editor and after a level is closed: obj gc)
$gc = "import unreal; unreal.SystemLibrary.execute_console_command(None, 'obj gc'); print('obj gc')"
& $py $ex -c $open 2>$null | Out-Null
& $py $ex -c $gc 2>$null | Out-Null
& $py $ex -c ($cvar -f 0) 2>$null | Out-Null
$pat = "WILDTEST done \| $tag \|"
$n0 = (Select-String -Path $log -Pattern $pat | Measure-Object).Count
$e0 = (Select-String -Path $log -Pattern "WILDTEST error" | Measure-Object).Count
$stop = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()"
$begin = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); print('pie requested')"
$isup = "import unreal; g = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); print('PIE', g.get_path_name() if g else None)"
& $py $ex -c $begin 2>$null | Out-Null
$up = $false
for ($k = 0; $k -lt 30 -and -not $up; $k++) {
    Start-Sleep 5
    $o = & $py $ex -c $isup 2>$null
    if ("$o" -match "UEDPIE_0_$L\.") { $up = $true }
    elseif ($k % 6 -eq 5 -and "$o" -notmatch "UEDPIE") { & $py $ex -c $begin 2>$null | Out-Null }
}
if (-not $up) { & $py $ex -c $stop 2>$null | Out-Null; Restore; "PIE did not start on ${L}: $o"; exit 1 }
Start-Sleep 8
$o = & $py $ex (Join-Path $PSScriptRoot "888_wilderness_test.py") $plan $tag 2>$null
if (-not ("$o" -match "wilderness test armed")) { & $py $ex -c $stop | Out-Null; Restore; "arm failed: $o"; exit 1 }
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
