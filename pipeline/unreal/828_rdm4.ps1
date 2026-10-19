# random_dungeonmagic_level4 test: opens the level the plan needs (random_dungeonmagic_level4_select for "select" or "menuui": the menu,
# which then opens the dungeon; random_dungeonmagic_level4 for the rest, and for "menufirst", whose play starts there and opens the menu),
# sets rd.HeroMenu (1 for "menufirst": the dungeon played without ?Hero= opens its menu; 0 otherwise: play stays in the dungeon with its
# DefaultHero), starts PIE, waits for the world the plan begins in, arms 827 with the plan, waits for a NEW "RDM4TEST done | <tag>" line,
# stops PIE, sets rd.HeroMenu back to 1 (what Play in the editor wants) and leaves the editor on random_dungeonmagic_level4.
# Args: plan tag [maxSeconds]   e.g.  .\828_rdm4.ps1 "menufirst,menuui,select,map" m1   .\828_rdm4.ps1 "heroes,inventory,mana,bonus,loot,potions,food,speed,noregen" r1
param([string]$plan, [string]$tag, [int]$maxs = 1200)
$py = $env:UE_PY; if (-not $py) { $py = "python" }
$ex = Join-Path $PSScriptRoot "..\blender_numpy\ue_exec.py"
$log = Join-Path $PSScriptRoot "..\..\claude_ue5\Saved\Logs\claude_ue5.log"
$M = "/Game/RandomDungeon/Maps/"
$first = $plan -match "menufirst"
$want = if ($first -or $plan -match "select|menuui") { "random_dungeonmagic_level4_select" } else { "random_dungeonmagic_level4" }
$edlevel = if ($first) { "random_dungeonmagic_level4" } else { $want }
$open = "import unreal; les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem); w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world(); print('LEVEL', w.get_name() == '{0}' or les.load_level('$M{0}'))"
$cvar = "import unreal; unreal.SystemLibrary.execute_console_command(None, 'rd.HeroMenu {0}'); print('rd.HeroMenu', unreal.SystemLibrary.get_console_variable_int_value('rd.HeroMenu'))"
function Restore { & $py $ex -c ($cvar -f 1) 2>$null | Out-Null }
& $py $ex -c ($open -f $edlevel) 2>$null | Out-Null
& $py $ex -c ($cvar -f $(if ($first) { 1 } else { 0 })) 2>$null | Out-Null
$pat = "RDM4TEST done \| $tag \|"
$n0 = (Select-String -Path $log -Pattern $pat | Measure-Object).Count
$e0 = (Select-String -Path $log -Pattern "RDM4TEST error" | Measure-Object).Count
$stop = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()"
$begin = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); print('pie requested')"
$isup = "import unreal; g = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world(); print('PIE', g.get_path_name() if g else None)"
& $py $ex -c $begin 2>$null | Out-Null
$up = $false
for ($k = 0; $k -lt 30 -and -not $up; $k++) {
    Start-Sleep 5
    $o = & $py $ex -c $isup 2>$null
    if ("$o" -match "UEDPIE_0_$want\.") { $up = $true }
    elseif ($k % 6 -eq 5 -and "$o" -notmatch "UEDPIE") { & $py $ex -c $begin 2>$null | Out-Null }
}
if (-not $up) { & $py $ex -c $stop 2>$null | Out-Null; Restore; "PIE did not start on ${want}: $o"; exit 1 }
Start-Sleep 8
$o = & $py $ex (Join-Path $PSScriptRoot "827_rdm4_test.py") $plan $tag 2>$null
if (-not ("$o" -match "rdm4 test armed")) { & $py $ex -c $stop | Out-Null; Restore; "arm failed: $o"; exit 1 }
$t = 0; $line = $null
while ($t -lt $maxs) {
    Start-Sleep 10; $t += 10
    if (-not (Get-Process UnrealEditor -ErrorAction SilentlyContinue)) { "EDITOR GONE"; exit 1 }
    $all = Select-String -Path $log -Pattern $pat
    if (($all | Measure-Object).Count -gt $n0) { $line = ($all | Select-Object -Last 1).Line; break }
    $err = Select-String -Path $log -Pattern "RDM4TEST error"
    if (($err | Measure-Object).Count -gt $e0) { $line = ($err | Select-Object -Last 1).Line; break }
}
Start-Sleep 3; & $py $ex -c $stop 2>$null | Out-Null; Start-Sleep 6
Restore
if ($edlevel -ne "random_dungeonmagic_level4") { & $py $ex -c ($open -f "random_dungeonmagic_level4") 2>$null | Out-Null }
if ($line) { $line.Substring($line.IndexOf("RDM4TEST")) } else { "no result after $maxs s"; (Select-String -Path $log -Pattern "RDM4TEST " | Select-Object -Last 5).Line }
