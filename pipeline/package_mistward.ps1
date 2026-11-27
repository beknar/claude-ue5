# Package the current game (the hero menu, Brokenspire with its wilderness and cities, mistward_castle, and the cities' dungeons vel_morrath, war_engine and sewers) as a standalone Windows game: one directory with claude_ue5.exe that runs on a PC without
# Unreal, Visual Studio or any runtime installed. Close the editor first (package_starship.ps1's way):
#   - builds the game target (Shipping) against the installed engine, cooks the six maps ($maps below) and what they refer
#     to, stages it into .pak / IoStore containers and archives it to
#     <repo>\builds\mistward_castle\Windows
#   - every map is named to the cook: the menu opens the town, the town the castle and (from Vel Morrath's cathedral) the
#     catacombs (vel_morrath), Ashenreach's foundry The War Engine (war_engine), Graymourne's sewer gate the sewers (sewers),
#     and the castle's Escape menu the menu, all by name (a string, which the cooker does not follow)
#   - the Visual C++ and Universal C runtime DLLs are copied next to the executable (app-local prerequisites) instead of
#     the redistributable installer, so nothing has to be installed on the PC that plays it
#   - for the cook and the stage only, the project's default map is the hero menu (a packaged game starts on its default
#     map) and the default game mode the C++ hero game mode (each map sets its own; the project's default, Fig4's Blueprint,
#     would pull its level's content into the cook). DefaultEngine.ini is put back afterwards, whatever happens.
# The package holds cooked content of the Fab packs: it stays out of the repository (builds/ is ignored).
#   - the cook fails on any error logged, and the asset registry logs 15 at every start: Kitchen_Asset_Kit textures (and two of Favelas's sequences) that are
#     zeros from their first byte (not packages; no map here uses them). The cook runs with -IgnoreCookErrors and the
#     script fails it itself on any other error in the cook's summary (KNOWN_BAD below). The whole output is kept in
#     <Out>\package.log.
# Args: [-Config Shipping|Development] [-Out <directory>] [-Test] (start the packaged game in each of its places in turn
#   ($runs below: the menu, the town, the castle, each city by fast travel and each dungeon down from its city, without a
#   window; then two runs in a window that takes the keyboard: a display setting, and the console typed into through
#   Slate; last the wilds played by the game itself for about half an hour: out of the gate, a journey, a save and load, a
#   20-minute walk with its memory), and check that each got there, kept running and left no crash report) [-TestOnly] (only that) [-SkipCook]
#   (stage and archive the last cook's output: after a cook that finished but was failed for its errors) [-Only <name,...>]
#   (the test's runs of those names only, e.g. -Only console,kethrys)
param([string]$Config = "Shipping", [string]$Out = "", [switch]$Test, [switch]$TestOnly, [switch]$SkipCook, [string[]]$Only = @())
# (2026-11-08: two of the Favelas pack's level sequences are zeros as well; no map here uses them)
$KNOWN_BAD = 'LogAssetRegistry: Error: Package is unloadable: .*/Content/(Kitchen_Asset_Kit/|Favelas/Sequencers/(LS_)?OverViewLevelSequence\.uasset)'
$repo = Split-Path -Parent $PSScriptRoot
$ue = "E:\Program Files\Epic Games\UE_5.8"
$proj = "$repo\claude_ue5\claude_ue5.uproject"
$maps = "/Game/RandomDungeon/Maps/mistward_castle_select", "/Game/RandomDungeon/Maps/brokenspire", "/Game/RandomDungeon/Maps/mistward_castle", "/Game/RandomDungeon/Maps/vel_morrath", "/Game/RandomDungeon/Maps/war_engine", "/Game/RandomDungeon/Maps/sewers", "/Game/RandomDungeon/Maps/kethrys_spire", "/Game/RandomDungeon/Maps/heaven_fortress", "/Game/RandomDungeon/Maps/caves", "/Game/RandomDungeon/Maps/heaven_tower", "/Game/RandomDungeon/Maps/town_building"
if (-not $Out) { $Out = "$repo\builds\mistward_castle" }
# (a relative -Out is the caller's folder: handed on as it is, UnrealAutomationTool archived it under the engine's own folder)
elseif (-not [IO.Path]::IsPathRooted($Out)) { $Out = Join-Path (Get-Location).Path $Out }
$exe = "$Out\Windows\claude_ue5.exe"
if (-not $TestOnly) {
    if (Get-Process UnrealEditor -ErrorAction SilentlyContinue) { "close the editor first"; exit 1 }
    # (UnrealBuildTool's SwarmInterface rules want a .NET Framework SDK: the same stand-in as build_cpp.ps1)
    $hasNetFx = Test-Path "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Microsoft SDKs\NETFXSDK\4.6.2"
    if (-not $hasNetFx -and -not $env:UE_SDKS_ROOT) {
        $root = Join-Path $env:TEMP "claude_ue5_autosdk"
        $inc = Join-Path $root "HostWin64\Win64\Windows Kits\NETFXSDK\4.6.2\Include\um"
        New-Item -ItemType Directory -Force $inc | Out-Null
        New-Item -ItemType Directory -Force (Join-Path $root "HostWin64\Win64\Windows Kits\NETFXSDK\4.6.2\Lib\um\x64") | Out-Null
        if (-not (Test-Path "$inc\mscoree.h")) { Set-Content -Path "$inc\mscoree.h" -Value "// stand-in for UnrealBuildTool (SwarmInterface rules)" }
        $env:UE_SDKS_ROOT = $root
    }
    $ini = "$repo\claude_ue5\Config\DefaultEngine.ini"
    $enc = New-Object Text.UTF8Encoding $false
    $keep = [IO.File]::ReadAllText($ini)
    $code = 1
    try {
        $t = $keep -replace '(?m)^GameDefaultMap=.*$', "GameDefaultMap=$($maps[0]).mistward_castle_select"
        $t = $t -replace '(?m)^GlobalDefaultGameMode=.*$', 'GlobalDefaultGameMode=/Script/claude_ue5.RDHeroGameMode'
        if ($t -eq $keep) { "DefaultEngine.ini: no GameDefaultMap / GlobalDefaultGameMode to set"; exit 1 }
        [IO.File]::WriteAllText($ini, $t, $enc)
        New-Item -ItemType Directory -Force $Out | Out-Null
        # (an array always: a one-item if-expression comes back a string, and splatting a string passes it letter by letter)
        [string[]]$cook = if ($SkipCook) { "-skipcook" } else { "-cook", "-IgnoreCookErrors" }
        & "$ue\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun "-project=$proj" -noP4 -utf8output -unattended -platform=Win64 "-clientconfig=$Config" `
            -build -nocompileeditor @cook "-map=$($maps -join '+')" -stage -pak -iostore -compressed -nodebuginfo `
            "-applocaldirectory=$ue\Engine\Binaries\ThirdParty\AppLocalDependencies" -archive "-archivedirectory=$Out" | Tee-Object -FilePath "$Out\package.log"
        $code = $LASTEXITCODE
    }
    finally { [IO.File]::WriteAllText($ini, $keep, $enc) }
    if ($code -ne 0) { "PACKAGE FAILED ($code)"; exit $code }
    if (-not $SkipCook) {
        # (the cook's summary: every error in it must be one of the known unreadable files)
        $log = Get-Content "$Out\package.log"
        $at = ($log | Select-String "Warning/Error Summary" | Select-Object -Last 1).LineNumber
        $errs = if ($at) { $log[$at..($log.Count - 1)] | Where-Object { $_ -match ': Error: ' } } else { @() }
        $other = @($errs | Where-Object { $_ -notmatch $KNOWN_BAD })
        "cook errors: {0} known (Kitchen_Asset_Kit's unreadable files), {1} other" -f (@($errs).Count - $other.Count), $other.Count
        if (-not ($log | Select-String "Packages Remain 0 ")) { "COOK FAILED: not every package was cooked"; exit 1 }
        if ($other.Count) { $other | Select-Object -First 20; "COOK FAILED: errors other than the known ones"; exit 1 }
    }
    $files = Get-ChildItem "$Out\Windows" -Recurse -File
    "packaged: $exe  ({0:N0} MB in {1} files)" -f (($files | Measure-Object Length -Sum).Sum / 1MB), $files.Count
}
if ($Test -or $TestOnly) {
    if (-not (Test-Path $exe)) { "no package at $exe"; exit 1 }
    $crashes = Join-Path $env:LOCALAPPDATA "claude_ue5\Saved\Crashes"
    $bad = 0
    # (the runs start at 1280 x 720 and the game saves that in its settings: the user's next game then ran at 1280 x 720 on
    #  a 3840 x 2160 screen and Game Bar recorded it in a corner of its frame. The settings are kept and put back.
    #  Shipping's are in LocalAppData, a Development game's beside it.)
    $gus = @((Join-Path $env:LOCALAPPDATA "claude_ue5\Saved\Config\Windows\GameUserSettings.ini"), (Join-Path $Out "Windows\claude_ue5\Saved\Config\Windows\GameUserSettings.ini"))
    # (as byte arrays: a plain if-expression unrolled an empty file's bytes to $null, and it was then removed, not put back)
    $kept = @{}; foreach ($g in $gus) { $kept[$g] = if (Test-Path $g) { , [byte[]][IO.File]::ReadAllBytes($g) } else { $null } }
    # (the window's inside measured as the game's own pixels: this script runs unaware of the screen's scaling)
    Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class RDWin {
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr c);
    [DllImport("user32.dll")] public static extern bool GetClientRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern uint GetDpiForWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern uint GetDpiForSystem();
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int cx, int cy, uint flags);
}
'@
    # (the castle writes a mark when it begins (-RDMarkFile): a run that stayed on the menu had passed as the castle's)
    $mark = Join-Path $env:TEMP "rd_package_mark.txt"
    $ctest = Join-Path $env:TEMP "rd_package_console.txt"
    $wtest = Join-Path $env:TEMP "rd_package_wild.txt"
    # (the wild run saves, loads and may autosave: the packaged game's saves (Shipping's in LocalAppData, a Development
    #  game's beside it) are kept and put back, so the player's own are as they were)
    $saveDirs = @((Join-Path $env:LOCALAPPDATA "claude_ue5\Saved\SaveGames"), (Join-Path $Out "Windows\claude_ue5\Saved\SaveGames"))
    $savesKept = Join-Path $env:TEMP "rd_package_saves_kept"; $savesTaken = $false
    $putSaves = {
        for ($i = 0; $i -lt $saveDirs.Count; $i++) {
            $k = Join-Path $savesKept "$i"
            if (Test-Path $saveDirs[$i]) { Remove-Item $saveDirs[$i] -Recurse -Force }
            if (Test-Path $k) { Copy-Item $k $saveDirs[$i] -Recurse }
        }
        # (put back: the kept folder goes, so that one found at the next run's start is always a stopped run's)
        Remove-Item $savesKept -Recurse -Force
    }
    # (the runs: the menu and the castle offscreen for 90 s each; then the castle in a window of its own with a display
    #  setting asked as the Escape menu's Apply sets it (-RDApplyDisplay: 1600 x 900, windowed), its window measured)
    # (into the castle through the menu, -RDStartHero: a Shipping game drops a map named on its command line (the engine's
    #  GameInstance: "In shipping don't allow a map override"), and its "castle" run had stayed on the menu since 2026-10-27)
    # (Brokenspire, 2026-11-02: the menu opens the town; -RDTownGo=castle walks her on through the Mistgate into the castle;
    #  -RDTownGo=catacombs (2026-11-06) takes her down into Vel Morrath's catacombs from the town, -RDTownGo=town:velmorrath
    #  out to the holy city, its mark written once the city is built round her)
    $runs = @(@{ name = "menu"; args = @(); secs = 90 }, @{ name = "town"; args = @("-RDStartHero=Warrior", "-RDMarkFile=$mark"); secs = 60; castle = $true; map = "brokenspire" },
              @{ name = "castle"; args = @("-RDStartHero=Warrior", "-RDTownGo=castle", "-RDMarkFile=$mark"); secs = 90; castle = $true; map = "mistward_castle" },
              @{ name = "catacombs"; args = @("-RDStartHero=Warrior", "-RDTownGo=catacombs", "-RDAllKeys", "-RDMarkFile=$mark"); secs = 90; castle = $true; map = "vel_morrath" },
              @{ name = "city"; args = @("-RDStartHero=Warrior", "-RDTownGo=town:velmorrath", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "town|Vel Morrath|Warrior*" },
              # (2026-11-08b: the dungeons open in order, each with its key (RD/RDKeys.cpp): the runs that go down take -RDAllKeys)
# (2026-11-07: Ashenreach's War Engine and Graymourne's sewers, down from the town by -RDTownGo=dungeon:<town>
              #  (DescendToCatacombs with that town's level), and out to both cities)
              @{ name = "war_engine"; args = @("-RDStartHero=Warrior", "-RDTownGo=dungeon:ashenreach", "-RDAllKeys", "-RDMarkFile=$mark"); secs = 90; castle = $true; map = "war_engine" },
              @{ name = "sewers"; args = @("-RDStartHero=Warrior", "-RDTownGo=dungeon:graymourne", "-RDAllKeys", "-RDMarkFile=$mark"); secs = 90; castle = $true; map = "sewers" },
    @{ name = "kethrys_spire"; args = @("-RDStartHero=Warrior", "-RDTownGo=dungeon:kethrysspire", "-RDAllKeys", "-RDMarkFile=$mark"); secs = 90; castle = $true; map = "kethrys_spire" },
    @{ name = "heaven_fortress"; args = @("-RDStartHero=Warrior", "-RDTownGo=dungeon:heaven", "-RDAllKeys", "-RDMarkFile=$mark"); secs = 90; castle = $true; map = "heaven_fortress" },
# (2026-11-25, the list of 2026-11-22's phase 27: the fortress's open tiers: down into it, tier 3 opened and a set of it generated round
# her (-RDOpen27, RD/RDAlien27.cpp); its mark once the sky is up: "open27|open=1|ground=...|clusters=...|... sky=1.00|<hero>")
@{ name = "fortress_open"; args = @("-RDStartHero=Warrior", "-RDTownGo=dungeon:heaven", "-RDAllKeys", "-RDOpen27", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "open27|open=1*sky=*|Warrior*" },          # (the mark is written once the sky is 0.99 or more (RDAlien27.cpp): 0.99 read as a failure in the list of 2026-11-26's package)
    # (2026-11-21: the caves under the landmark towers (935): down into the cave level at tier 12 from where she stands)
    @{ name = "caves"; args = @("-RDStartHero=Warrior", "-RDTownGo=cave:12", "-RDMarkFile=$mark"); secs = 90; castle = $true; map = "caves" },
# (2026-11-22, the list of 2026-11-20's eighteenth phase: the wilds' runs (RD/RDList15q.cpp): her horse called, mounted and ridden 15 s
# 3 km out ("horse|<metres>|<still mounted>"); the nearest village reached by the map's travel, its households standing ("village|<name>|
# <people>"); the nearest broken tower, into its cave by its mouth as F takes her (the caves level's own mark))
@{ name = "horse"; args = @("-RDStartHero=Warrior", "-RDTownGo=horse", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "horse|*|1|Warrior*"; minM = 20; saves = $true },
@{ name = "village"; args = @("-RDStartHero=Warrior", "-RDTownGo=village", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "village|*|*|Warrior*"; saves = $true },
@{ name = "cavetower"; args = @("-RDStartHero=Warrior", "-RDTownGo=cavetower", "-RDMarkFile=$mark"); secs = 180; castle = $true; map = "caves"; saves = $true },
              @{ name = "ashenreach"; args = @("-RDStartHero=Warrior", "-RDTownGo=town:ashenreach", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "town|Ashenreach|Warrior*" },
              @{ name = "graymourne"; args = @("-RDStartHero=Warrior", "-RDTownGo=town:graymourne", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "town|Graymourne|Warrior*" },
              # (2026-11-10: the last two cities by fast travel too, Kethrys Spire and Heaven: their dungeons were run, the cities not)
              @{ name = "kethrys"; args = @("-RDStartHero=Warrior", "-RDTownGo=town:kethrysspire", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "town|Kethrys Spire|Warrior*" },
              @{ name = "heaven"; args = @("-RDStartHero=Warrior", "-RDTownGo=town:heaven", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "town|Heaven|Warrior*" },
              # (the list of 2026-11-22's phase 24: out to Heaven and in by its first tower's door, the tower built round her)
              @{ name = "tower"; args = @("-RDStartHero=Warrior", "-RDTownGo=tower", "-RDMarkFile=$mark"); secs = 210; castle = $true; want = "tower|*|Warrior*" },
# (the list of 2026-11-26's ninth phase: Brokenspire built in Closed Structures, in by the general store's door (F), its level laid round her:
#  "closed|<the building>|<pieces laid>|<panes>|<hero>")
@{ name = "closed"; args = @("-RDStartHero=Warrior", "-RDStructures=closed", "-RDTownGo=closed", "-RDMarkFile=$mark"); secs = 150; castle = $true; want = "closed|?*|[1-9]*|*|Warrior*" },
              @{ name = "display"; args = @("-RDStartHero=Warrior", "-RDMarkFile=$mark", "-RDApplyDisplay=1600x900x2"); secs = 30; window = $true; castle = $true },
              # (2026-11-08: the game's own console (RD/RDConsole.cpp), in a window of its own (the keys go to its focused line):
              #  its self-test types into it through Slate and writes what it measured, and its picture beside it; -RDConsole: it is
              #  off by default where Unreal's own console is, a Development game (2026-11-10: the Development package's run failed))
              @{ name = "console"; args = @("-RDStartHero=Warrior", "-RDMarkFile=$mark", "-RDConsoleTest=$ctest", "-RDConsole", "-windowed", "-ResX=1280", "-ResY=720"); secs = 75; shown = $true; console = $true; castle = $true; map = "brokenspire" },
              # (2026-11-14, the TODO sweep: the wilds in the packaged game (RD/RDWildSelfTest.cpp): from the square out of the
              #  gate, a journey to Vel Morrath, a save, moved 300 m off and loaded, then a 20-minute walk with its memory and frame
              #  rate every 30 s; it writes "stage|..." lines and ends with "result|ok". The run ends when the result is written.)
              @{ name = "wild"; args = @("-RDStartHero=Warrior", "-RDWildTest=$wtest", "-RDWildTestMinutes=20"); secs = 2700; wild = $true })
    if ($Only.Count) { $Only = @($Only | ForEach-Object { $_ -split "," }); $runs = @($runs | Where-Object { $Only -contains $_.name }) }
    try {
    foreach ($run in $runs) {
        $before = @(Get-ChildItem $crashes -Directory -ErrorAction SilentlyContinue).Count
        if (Test-Path $mark) { Remove-Item $mark -Force }
        # (the display run's "saved" must come from this run: the settings files are taken away first (put back at the end))
        if ($run.window) { foreach ($g in $gus) { if (Test-Path $g) { Remove-Item $g -Force } } }
        if ($run.console) { foreach ($f in @($ctest, [IO.Path]::ChangeExtension($ctest, "png"))) { if (Test-Path $f) { Remove-Item $f -Force } } }
        if ($run.wild -and (Test-Path $wtest)) { Remove-Item $wtest -Force }
        # (PR #110's review: the wilds' runs autosave too (the horse owned, a village found): their saves are taken and put back as the walk's)
        if ($run.wild -or $run.saves) {
            # (PR #64's review: a kept folder left over is a run stopped before it put them back (killed, the machine short of
            #  memory): it holds the player's saves and the save folders the test's, so it is kept and taken as the player's)
            if (Test-Path $savesKept) { "    the player's saves kept by a run that was stopped: put back from $savesKept at the end" }
            else { New-Item -ItemType Directory -Force $savesKept | Out-Null
                   for ($i = 0; $i -lt $saveDirs.Count; $i++) { if (Test-Path $saveDirs[$i]) { Copy-Item $saveDirs[$i] (Join-Path $savesKept "$i") -Recurse } } }
            $savesTaken = $true
        }
        $client = $null; $least = $null; $saved = $null; $dpi = 0; $want = "1600x900"
        # (claude_ue5.exe is a launcher: the game is the exe under claude_ue5\Binaries\Win64, which it starts and waits for:
        #  claude_ue5-Win64-Shipping.exe, but in a Development package claude_ue5.exe too: found by its folder, not its name
        #  (by the Shipping name the Development games were never found, nor stopped))
        $bin = (Join-Path $Out "Windows\claude_ue5\Binaries\Win64").ToLower()
        $t0 = Get-Date
        $extra = if ($run.window -or $run.shown) { @("-nosound") } else { @("-RenderOffScreen", "-ResX=1280", "-ResY=720", "-nosound") }
        $l = Start-Process -FilePath $exe -ArgumentList ($run.args + $extra) -PassThru
        $p = $null
        for ($s = 0; $s -lt 30 -and -not $p; $s++) { Start-Sleep 1; $p = Get-Process "claude_ue5*" -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.ToLower().StartsWith($bin) -and $_.StartTime -ge $t0.AddSeconds(-1) } | Select-Object -First 1 }
        [long]$peak = 0; $mem = @()
        if ($p) { for ($s = 0; $s -lt $run.secs -and -not $p.HasExited; $s += 5) { Start-Sleep 5; $p.Refresh(); if (-not $p.HasExited) { $peak = [math]::Max($peak, $p.WorkingSet64); if (-not $run.wild -or $s % 60 -eq 0) { $mem += [int]($p.WorkingSet64 / 1MB) } }
            # (the wild run is over when its result is written)
            if ($run.wild -and (Test-Path $wtest) -and (Select-String -Path $wtest -Pattern '^result\|' -Quiet)) { break } } }
        $alive = $p -and -not $p.HasExited
        if ($run.window -and $alive) {
            [void][RDWin]::SetThreadDpiAwarenessContext([IntPtr](-4)); $r = New-Object RDWin+RECT
            if ([RDWin]::GetClientRect($p.MainWindowHandle, [ref]$r)) { $client = "$($r.R - $r.L)x$($r.B - $r.T)" }
            # (the size in the screen's real pixels, and the window handling the screen's scaling itself (its DPI the screen's):
            #  unaware of it (the engine's default), Windows stretched a 1600 x 900 window to 3200 x 1800 on a 200 % screen)
            $dpi = [RDWin]::GetDpiForWindow($p.MainWindowHandle)
            # (the settings read before the window is shrunk below (a resize may be saved as the resolution))
            $saved = $gus | Where-Object { Test-Path $_ } | ForEach-Object { Select-String -Path $_ -Pattern '^ResolutionSizeX=1600' } | Select-Object -First 1
            # (the least size (PR #51's review): the window asked to 400 x 300 as a drag would, its inside read: 960 x 540 of the
            #  screen's pixels, the frame outside it)
            [void][RDWin]::SetWindowPos($p.MainWindowHandle, [IntPtr]::Zero, 0, 0, 400, 300, 0x16); Start-Sleep 2
            $r2 = New-Object RDWin+RECT; if ([RDWin]::GetClientRect($p.MainWindowHandle, [ref]$r2)) { $least = "$($r2.R - $r2.L)x$($r2.B - $r2.T)" }
        }
        if ($run.name -ne "menu" -and -not $run.window) { "memory every $(if ($run.wild) { 60 } else { 5 }) s (MB): $($mem -join ' ')" }
        foreach ($q in @($p, $l)) { if ($q -and -not $q.HasExited) { Stop-Process -Id $q.Id -Force -Confirm:$false } }
        Start-Sleep 2
        $after = @(Get-ChildItem $crashes -Directory -ErrorAction SilentlyContinue).Count
        $ok = $alive -and $after -eq $before
        # (where the run got to: the castle's mark, "castle|<map>|<hero>")
        $where = if (Test-Path $mark) { (Get-Content $mark -Raw).Trim() } else { "no mark (not the castle)" }
        # (the city's run: the town writes its mark once the wilderness town is built round her, "town|<name>|<hero>")
        $pat = if ($run.want) { $run.want } else { "castle|$(if ($run.map) { $run.map } else { '*' })|Warrior*" }
        if ($run.castle) { $ok = $ok -and $where -like $pat }
        # (PR #110's review: a ride of 0 m mounted had passed: the horse's metres, "horse|<m>|<mounted>", at least minM)
        if ($run.minM) { $f = $where.Split('|'); $ok = $ok -and $f.Count -ge 3 -and [double]$f[1] -ge $run.minM }
        if ($run.saves -and $savesTaken) { & $putSaves; $savesTaken = $false; "    the game's saves put back as they were" }
        if ($run.console) {
            # (its self-test's lines: "check|<name>|ok/FAILED|<measured>", the last "result|ok")
            $lines = if (Test-Path $ctest) { @(Get-Content $ctest -Encoding UTF8) } else { @() }
            $lines | Where-Object { $_ -like "check|*" -or $_ -like "note|*" } | ForEach-Object { "    $_" }
            $png = [IO.Path]::ChangeExtension($ctest, "png")
            "    picture: $(if (Test-Path $png) { $png } else { 'none' })"
            $ok = $ok -and $lines.Count -gt 0 -and $lines[-1] -eq "result|ok"
        }
        if ($run.wild) {
            # (its lines: "stage|<name>|ok/FAILED|<measured>", "mem|<s>|<MB>|<km>|<chunks>|<fps>", the last "result|ok"; the game
            #  is stopped once the result is written, so "alive" is not asked of it)
            $lines = if (Test-Path $wtest) { @(Get-Content $wtest -Encoding UTF8) } else { @() }
            $lines | ForEach-Object { "    $_" }
            $ok = $after -eq $before -and $lines.Count -gt 0 -and $lines[-1] -eq "result|ok"
            $alive = $alive -or $ok
            & $putSaves; $savesTaken = $false
            "    the game's saves put back as they were"
        }
        if ($run.window) {
            # (the window's inside the size asked, its scaling the screen's (the game handles it; unaware it read 96 on a
            #  200 % screen), and this run's settings say so: Apply as the menu's)
            $sys = [RDWin]::GetDpiForSystem()
            $ok = $ok -and $client -eq $want -and $dpi -eq $sys -and [bool]$saved -and $least -eq "960x540"
            "TEST display: {0} | {5} | window inside {1} pixels (asked {4} windowed) | its scaling {3} %, the screen's {6} % | saved in this run's settings: {2} | shrunk to 400 x 300: {7} inside (least 960x540)" -f ($(if ($ok) { "ok" } else { "FAILED" })), $client, [bool]$saved, [int]($dpi * 100 / 96), $want, $where, [int]($sys * 100 / 96), $least
        }
        else { "TEST {0}: {1} | ran {6} s: {2} | exit code {3} | new crash reports {4} | peak memory {5:N0} MB{7}" -f $run.name, ($(if ($ok) { "ok" } else { "FAILED" })), $alive, ($(if ($alive) { "-" } else { $p.ExitCode })), ($after - $before), ($peak / 1MB), $run.secs, $(if ($run.castle) { " | $where" } else { "" }) }
        if (-not $ok) { $bad++ }
    }
    }
    finally {
        # (put back whatever stopped the runs: an interrupted test left the user's next game at the test's size)
        foreach ($g in $gus) { if ($null -ne $kept[$g]) { [IO.File]::WriteAllBytes($g, $kept[$g]) } elseif (Test-Path $g) { Remove-Item $g -Force } }
        "the game's settings put back as they were"
        if ($savesTaken) { & $putSaves; "the game's saves put back as they were" }
    }
    if ($bad) { exit 1 }
}
exit 0
