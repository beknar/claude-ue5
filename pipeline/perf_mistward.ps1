# The frame rate of the packaged game in every city and every biome (the list of 2026-11-22: docs/performance.md, before and after its
# changes). Runs a package built by package_mistward.ps1 with -RDPerf (RD/RDList16.cpp: each city's square and a street by the map's
# travel, then each biome at its nearest site to Brokenspire, settled 20 s and measured 15 s), full screen, at each resolution asked,
# then writes the results into docs/performance.md under the heading given (pipeline/blender_numpy/perf_doc.py).
# Args: -Out <package directory> (default builds\mistward_castle) -Label "BEFORE LIST16 changes" [-Res 3840x2160,1920x1080] (default:
#   the desktop's alone: at the engine's default screen percentage a 4K screen renders about 1920 x 1080 before its upscale, and the
#   two read the same in BEFORE's first run) [-Py <python>] [-NoDoc] (measure only)
param([string]$Out = "", [string]$Label = "BEFORE LIST16 changes", [string[]]$Res = @(), [string]$Py = "python", [switch]$NoDoc)
$repo = Split-Path -Parent $PSScriptRoot
if (-not $Out) { $Out = "$repo\builds\mistward_castle" } elseif (-not [IO.Path]::IsPathRooted($Out)) { $Out = Join-Path (Get-Location).Path $Out }
$exe = "$Out\Windows\claude_ue5.exe"
if (-not (Test-Path $exe)) { "no package at $exe"; exit 1 }
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class RDPerfWin {
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr c);
    [DllImport("user32.dll")] public static extern int GetSystemMetrics(int i);
}
'@
if ($Res.Count -eq 0) {
    # (the desktop's own pixels, aware of the screen's scaling: unaware, a 200 % screen reads half its size)
    [void][RDPerfWin]::SetThreadDpiAwarenessContext([IntPtr](-4))
    $desk = "{0}x{1}" -f [RDPerfWin]::GetSystemMetrics(0), [RDPerfWin]::GetSystemMetrics(1)
    $Res = @($desk)
}
$Res = @($Res | ForEach-Object { $_ -split "," })
# (the runs travel and autosave, and set the resolution: the player's settings and saves are kept and put back, as package_mistward.ps1 does)
$gus = @((Join-Path $env:LOCALAPPDATA "claude_ue5\Saved\Config\Windows\GameUserSettings.ini"), (Join-Path $Out "Windows\claude_ue5\Saved\Config\Windows\GameUserSettings.ini"))
$saveDirs = @((Join-Path $env:LOCALAPPDATA "claude_ue5\Saved\SaveGames"), (Join-Path $Out "Windows\claude_ue5\Saved\SaveGames"))
$savesKept = Join-Path $env:TEMP "rd_perf_saves_kept"
# (the settings are kept in the same folder as the saves (PR #111's review): a run stopped before it put them back leaves both there, and
#  the next run takes them as the player's, not the stopped run's)
$kept = @{}
if (Test-Path $savesKept) { "the player's saves and settings kept by a run that was stopped: put back from $savesKept at the end" }
else {
    New-Item -ItemType Directory -Force $savesKept | Out-Null
    for ($i = 0; $i -lt $saveDirs.Count; $i++) { if (Test-Path $saveDirs[$i]) { Copy-Item $saveDirs[$i] (Join-Path $savesKept "$i") -Recurse } }
    for ($i = 0; $i -lt $gus.Count; $i++) { if (Test-Path $gus[$i]) { Copy-Item $gus[$i] (Join-Path $savesKept "gus$i.ini") } else { Set-Content -Path (Join-Path $savesKept "gus$i.none") -Value "" } }
}
for ($i = 0; $i -lt $gus.Count; $i++) { $k = Join-Path $savesKept "gus$i.ini"; $kept[$gus[$i]] = if (Test-Path $k) { , [byte[]][IO.File]::ReadAllBytes($k) } else { $null } }
$bin = (Join-Path $Out "Windows\claude_ue5\Binaries\Win64").ToLower()
$files = @()
$bad = 0
try {
    foreach ($r in $Res) {
        $w, $h = $r -split "x"
        $file = Join-Path $env:TEMP "rd_perf_$r.txt"
        if (Test-Path $file) { Remove-Item $file -Force }
        $shots = Join-Path $env:TEMP "rd_perf_$($r)_shots"
        if (Test-Path $shots) { Remove-Item $shots -Recurse -Force }
        # (BEFORE's places at this resolution, replayed by the later runs)
        $tag = $Label -replace '[^A-Za-z0-9]+', '_'
        $placesFrom = Join-Path $repo "claude_ue5\SourceArt\perf16\perf_BEFORE_LIST16_changes_$r.txt"
        $replay = if ($tag -notlike "BEFORE*" -and (Test-Path $placesFrom)) { @("-RDPerfPlaces=$placesFrom") } else { @() }
        # (the wilds' level (the cities and biomes), then the castle's and Heaven's fortress's first hall: the same file, one after the other)
        foreach ($leg in @(@(), @("-RDTownGo=castle"), @("-RDTownGo=dungeon:heaven", "-RDAllKeys"))) {
            $t0 = Get-Date
            $before = if (Test-Path $file) { @(Get-Content $file).Count } else { 0 }
            $l = Start-Process -FilePath $exe -ArgumentList (@("-RDStartHero=Warrior", "-RDPerf=$file", "-ResX=$w", "-ResY=$h", "-fullscreen", "-nosound") + $replay + $leg) -PassThru
            $p = $null
            for ($s = 0; $s -lt 30 -and -not $p; $s++) { Start-Sleep 1; $p = Get-Process "claude_ue5*" -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.ToLower().StartsWith($bin) -and $_.StartTime -ge $t0.AddSeconds(-1) } | Select-Object -First 1 }
            # (at most 4 hours for the wilds' leg: 82 places of about 1.5 minutes each and the slow first loads; 15 minutes a hall)
            $limit = if ($leg.Count) { 900 } else { 14400 }
            if ($p) { for ($s = 0; $s -lt $limit -and -not $p.HasExited; $s += 10) { Start-Sleep 10; if ((Test-Path $file) -and @(Get-Content $file | Select-Object -Skip $before | Where-Object { $_ -eq 'perf|done' }).Count) { break } } }
            Start-Sleep 5
            foreach ($q in @($p, $l)) { if ($q -and -not $q.HasExited) { Stop-Process -Id $q.Id -Force -Confirm:$false } }
            Start-Sleep 3
        }
        $lines = if (Test-Path $file) { @(Get-Content $file -Encoding UTF8) } else { @() }
        $dones = @($lines | Where-Object { $_ -eq "perf|done" }).Count
        "PERF $r : {0} lines, {1} of 3 legs done" -f $lines.Count, $dones
        $lines | Where-Object { $_ -like "perf|*" } | ForEach-Object { "    $_" }
        if ($dones -lt 3) { $bad++ }
        if ($lines.Count) {
            $keep = Join-Path $repo "claude_ue5\SourceArt\perf16\perf_$($tag)_$r.txt"; New-Item -ItemType Directory -Force (Split-Path $keep) | Out-Null; Copy-Item $file $keep -Force; $files += $keep
            # (the pictures stay out of the repository: kept beside the package)
            $pk = Join-Path $Out "perf16_shots\$($tag)_$r"; if (Test-Path $shots) { New-Item -ItemType Directory -Force $pk | Out-Null; Copy-Item "$shots\*" $pk -Force; "    pictures: $pk" }
        }
    }
}
finally {
    foreach ($g in $gus) { if ($null -ne $kept[$g]) { [IO.File]::WriteAllBytes($g, $kept[$g]) } elseif (Test-Path $g) { Remove-Item $g -Force } }
    for ($i = 0; $i -lt $saveDirs.Count; $i++) { $k = Join-Path $savesKept "$i"; if (Test-Path $saveDirs[$i]) { Remove-Item $saveDirs[$i] -Recurse -Force }; if (Test-Path $k) { Copy-Item $k $saveDirs[$i] -Recurse } }
    Remove-Item $savesKept -Recurse -Force
    "the game's settings and saves put back as they were"
}
if (-not $NoDoc -and $files.Count) { & $Py "$repo\pipeline\blender_numpy\perf_doc.py" "$repo\docs\performance.md" $Label @files }
if ($bad) { exit 1 }
exit 0
