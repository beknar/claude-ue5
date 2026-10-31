# Package mistward_castle as a standalone Windows game: one directory with claude_ue5.exe that runs on a PC without
# Unreal, Visual Studio or any runtime installed. Close the editor first (package_starship.ps1's way):
#   - builds the game target (Shipping) against the installed engine, cooks the hero menu (mistward_castle_select) and the
#     castle (mistward_castle) and what they refer to, stages it into .pak / IoStore containers and archives it to
#     <repo>\builds\mistward_castle\Windows
#   - both maps are named to the cook: the menu opens the castle, and the castle's Escape menu the menu, by name (a string,
#     which the cooker does not follow)
#   - the Visual C++ and Universal C runtime DLLs are copied next to the executable (app-local prerequisites) instead of
#     the redistributable installer, so nothing has to be installed on the PC that plays it
#   - for the cook and the stage only, the project's default map is the hero menu (a packaged game starts on its default
#     map) and the default game mode the C++ hero game mode (each map sets its own; the project's default, Fig4's Blueprint,
#     would pull its level's content into the cook). DefaultEngine.ini is put back afterwards, whatever happens.
# The package holds cooked content of the Fab packs: it stays out of the repository (builds/ is ignored).
#   - the cook fails on any error logged, and the asset registry logs 13 at every start: Kitchen_Asset_Kit textures that are
#     zeros from their first byte (not packages; no map here uses them). The cook runs with -IgnoreCookErrors and the
#     script fails it itself on any other error in the cook's summary (KNOWN_BAD below). The whole output is kept in
#     <Out>\package.log.
# Args: [-Config Shipping|Development] [-Out <directory>] [-Test] (start the packaged game on the menu and in the castle,
#   without a window, and check that it keeps running and leaves no crash report) [-TestOnly] (only that) [-SkipCook]
#   (stage and archive the last cook's output: after a cook that finished but was failed for its errors)
param([string]$Config = "Shipping", [string]$Out = "", [switch]$Test, [switch]$TestOnly, [switch]$SkipCook)
$KNOWN_BAD = 'LogAssetRegistry: Error: Package is unloadable: .*/Content/Kitchen_Asset_Kit/'
$repo = Split-Path -Parent $PSScriptRoot
$ue = "E:\Program Files\Epic Games\UE_5.8"
$proj = "$repo\claude_ue5\claude_ue5.uproject"
$maps = "/Game/RandomDungeon/Maps/mistward_castle_select", "/Game/RandomDungeon/Maps/mistward_castle"
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
    foreach ($run in @(@{ name = "menu"; args = @() }, @{ name = "castle"; args = @("/Game/RandomDungeon/Maps/mistward_castle?Hero=Warrior") })) {
        $before = @(Get-ChildItem $crashes -Directory -ErrorAction SilentlyContinue).Count
        # (claude_ue5.exe is a launcher: the game is the exe under claude_ue5\Binaries\Win64, which it starts and waits for:
        #  claude_ue5-Win64-Shipping.exe, but in a Development package claude_ue5.exe too: found by its folder, not its name
        #  (by the Shipping name the Development games were never found, nor stopped))
        $bin = (Join-Path $Out "Windows\claude_ue5\Binaries\Win64").ToLower()
        $t0 = Get-Date
        $l = Start-Process -FilePath $exe -ArgumentList ($run.args + @("-RenderOffScreen", "-ResX=1280", "-ResY=720", "-nosound")) -PassThru
        $p = $null
        for ($s = 0; $s -lt 30 -and -not $p; $s++) { Start-Sleep 1; $p = Get-Process "claude_ue5*" -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.ToLower().StartsWith($bin) -and $_.StartTime -ge $t0.AddSeconds(-1) } | Select-Object -First 1 }
        [long]$peak = 0; $mem = @()
        if ($p) { for ($s = 0; $s -lt 90 -and -not $p.HasExited; $s += 5) { Start-Sleep 5; $p.Refresh(); if (-not $p.HasExited) { $peak = [math]::Max($peak, $p.WorkingSet64); $mem += [int]($p.WorkingSet64 / 1MB) } } }
        $alive = $p -and -not $p.HasExited
        if ($run.name -eq "castle") { "memory every 5 s (MB): $($mem -join ' ')" }
        foreach ($q in @($p, $l)) { if ($q -and -not $q.HasExited) { Stop-Process -Id $q.Id -Force -Confirm:$false } }
        Start-Sleep 2
        $after = @(Get-ChildItem $crashes -Directory -ErrorAction SilentlyContinue).Count
        $ok = $alive -and $after -eq $before
        if (-not $ok) { $bad++ }
        "TEST {0}: {1} | ran 90 s: {2} | exit code {3} | new crash reports {4} | peak memory {5:N0} MB" -f $run.name, ($(if ($ok) { "ok" } else { "FAILED" })), $alive, ($(if ($alive) { "-" } else { $p.ExitCode })), ($after - $before), ($peak / 1MB)
    }
    if ($bad) { exit 1 }
}
exit 0
