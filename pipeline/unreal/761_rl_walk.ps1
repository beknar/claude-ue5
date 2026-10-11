# random_level walk test: start PIE, arm 760 with a plan, wait for a NEW "RLWALK done | <tag>" line, stop PIE.
# Starting PIE streams in every start-square building interior and can keep the editor busy for a while, so the arm
# call is retried until 760 answers "walk test armed".
# Args: plan tag [maxSeconds]   e.g.  .\761_rl_walk.ps1 "expand:+x:400,visit:new:6,home,visit:start:8" w1
# Env: UE_PY = python with the remote-exec client's needs (default: python)
param([string]$plan, [string]$tag, [int]$maxs = 2400)
$py = $env:UE_PY; if (-not $py) { $py = "python" }
$ex = Join-Path $PSScriptRoot "..\blender_numpy\ue_exec.py"
$log = Join-Path $PSScriptRoot "..\..\claude_ue5\Saved\Logs\claude_ue5.log"
$pat = "RLWALK done \| $tag \|"
$n0 = (Select-String -Path $log -Pattern $pat | Measure-Object).Count
$stop = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_end_play()"
$begin = "import unreal; unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).editor_request_begin_play(); print('pie requested')"
$isup = "import unreal; print('PIE', unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_game_world() is not None)"
& $py $ex -c $begin 2>$null | Out-Null
# wait for the play world (a request sent while the editor is busy, e.g. right after a big save, can be dropped)
$up = $false
for ($k = 0; $k -lt 30 -and -not $up; $k++) {
    Start-Sleep 5
    $o = & $py $ex -c $isup 2>$null
    if ("$o" -match "PIE True") { $up = $true }
    elseif ($k % 6 -eq 5) { & $py $ex -c $begin 2>$null | Out-Null }
}
if (-not $up) { "PIE did not start"; exit 1 }
$armed = $false
for ($k = 0; $k -lt 20 -and -not $armed; $k++) {
    Start-Sleep 6
    $o = & $py $ex (Join-Path $PSScriptRoot "760_rl_walk_test.py") $plan $tag 2>$null
    if ("$o" -match "walk test armed") { $armed = $true }
    elseif ("$o" -match "REMOTE_FAILED") { & $py $ex -c $stop | Out-Null; "arm failed: $o"; exit 1 }
}
if (-not $armed) { & $py $ex -c $stop | Out-Null; "could not arm the walk test"; exit 1 }
$t = 0; $line = $null
while ($t -lt $maxs) {
    Start-Sleep 10; $t += 10
    if (-not (Get-Process UnrealEditor -ErrorAction SilentlyContinue)) { "EDITOR GONE"; exit 1 }
    $all = Select-String -Path $log -Pattern $pat
    if (($all | Measure-Object).Count -gt $n0) { $line = ($all | Select-Object -Last 1).Line; break }
}
Start-Sleep 3; & $py $ex -c $stop 2>$null | Out-Null; Start-Sleep 6
if ($line) { $line.Substring($line.IndexOf("RLWALK")) } else { "no result after $maxs s"; (Select-String -Path $log -Pattern "RLWALK " | Select-Object -Last 3).Line }
