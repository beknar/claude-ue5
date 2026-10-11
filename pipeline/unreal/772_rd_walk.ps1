# random_dungeon_level walk test: start PIE, arm 771 with a plan, wait for a NEW "RDWALK done | <tag>" line, stop PIE.
# Args: plan tag [maxSeconds]   e.g.  .\772_rd_walk.ps1 "rooms:5,expand:+x,rooms:4,home" w1
param([string]$plan, [string]$tag, [int]$maxs = 1200)
$py = $env:UE_PY; if (-not $py) { $py = "python" }
$ex = Join-Path $PSScriptRoot "..\blender_numpy\ue_exec.py"
$log = Join-Path $PSScriptRoot "..\..\claude_ue5\Saved\Logs\claude_ue5.log"
$pat = "RDWALK done \| $tag \|"
$n0 = (Select-String -Path $log -Pattern $pat | Measure-Object).Count
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
$o = & $py $ex (Join-Path $PSScriptRoot "771_rd_walk_test.py") $plan $tag 2>$null
if (-not ("$o" -match "walk test armed")) { & $py $ex -c $stop | Out-Null; "arm failed: $o"; exit 1 }
$t = 0; $line = $null
while ($t -lt $maxs) {
    Start-Sleep 10; $t += 10
    if (-not (Get-Process UnrealEditor -ErrorAction SilentlyContinue)) { "EDITOR GONE"; exit 1 }
    $all = Select-String -Path $log -Pattern $pat
    if (($all | Measure-Object).Count -gt $n0) { $line = ($all | Select-Object -Last 1).Line; break }
    if (Select-String -Path $log -Pattern "RDWALK error" -SimpleMatch | Where-Object { $_.LineNumber -gt 0 } | Select-Object -Last 1 | Where-Object { $_.Line -match "RDWALK error" -and $t -gt 15 }) { }
}
Start-Sleep 3; & $py $ex -c $stop 2>$null | Out-Null; Start-Sleep 6
if ($line) { $line.Substring($line.IndexOf("RDWALK")) } else { "no result after $maxs s"; (Select-String -Path $log -Pattern "RDWALK " | Select-Object -Last 5).Line }
