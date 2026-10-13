# random_dungeoncombat_level combat test: start PIE (the level must be the open one), arm 792 with a plan, wait for a NEW "RDCTEST done | <tag>" line, stop PIE.
# Args: plan tag [maxSeconds]   e.g.  .\793_rdc_combat.ps1 "setup,weapons,monsters,kill:3,hurt,tier,death,regen,map" c1
param([string]$plan, [string]$tag, [int]$maxs = 900)
$py = $env:UE_PY; if (-not $py) { $py = "python" }
$ex = Join-Path $PSScriptRoot "..\blender_numpy\ue_exec.py"
$log = Join-Path $PSScriptRoot "..\..\claude_ue5\Saved\Logs\claude_ue5.log"
$pat = "RDCTEST done \| $tag \|"
$n0 = (Select-String -Path $log -Pattern $pat | Measure-Object).Count
$e0 = (Select-String -Path $log -Pattern "RDCTEST error" | Measure-Object).Count
$stop = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()"
$begin = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); print('pie requested')"
$isup = "import unreal; print('PIE', unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)"
& $py $ex -c $begin 2>$null | Out-Null
$up = $false
for ($k = 0; $k -lt 30 -and -not $up; $k++) {
    Start-Sleep 5
    $o = & $py $ex -c $isup 2>$null
    if ("$o" -match "PIE True") { $up = $true }
    elseif ($k % 6 -eq 5) { & $py $ex -c $begin 2>$null | Out-Null }
}
if (-not $up) { "PIE did not start"; exit 1 }
Start-Sleep 8
$o = & $py $ex (Join-Path $PSScriptRoot "792_rdc_combat_test.py") $plan $tag 2>$null
if (-not ("$o" -match "combat test armed")) { & $py $ex -c $stop | Out-Null; "arm failed: $o"; exit 1 }
$t = 0; $line = $null
while ($t -lt $maxs) {
    Start-Sleep 10; $t += 10
    if (-not (Get-Process UnrealEditor -ErrorAction SilentlyContinue)) { "EDITOR GONE"; exit 1 }
    $all = Select-String -Path $log -Pattern $pat
    if (($all | Measure-Object).Count -gt $n0) { $line = ($all | Select-Object -Last 1).Line; break }
    $err = Select-String -Path $log -Pattern "RDCTEST error"
    if (($err | Measure-Object).Count -gt $e0) { $line = ($err | Select-Object -Last 1).Line; break }
}
Start-Sleep 3; & $py $ex -c $stop 2>$null | Out-Null; Start-Sleep 6
if ($line) { $line.Substring($line.IndexOf("RDCTEST")) } else { "no result after $maxs s"; (Select-String -Path $log -Pattern "RDCTEST " | Select-Object -Last 5).Line }
