# Package starship_level as a standalone Windows game: one directory with claude_ue5.exe that runs on a PC without
# Unreal, Visual Studio or any runtime installed. Close the editor first.
#   - builds the game target (Shipping) against the installed engine, cooks starship_level and what it refers to,
#     stages it into .pak / IoStore containers and archives it to <repo>\builds\starship_level\Windows
#   - the Visual C++ and Universal C runtime DLLs are copied next to the executable (app-local prerequisites) instead
#     of the redistributable installer, so nothing has to be installed on the PC that plays it
#   - for the cook and the stage only, the project's default map and game mode are starship_level's (the packaged game
#     starts on its default map; the cooker also takes in what the default game mode refers to). DefaultEngine.ini is
#     put back afterwards, whatever happens.
# The package holds cooked content of the Fab packs: it stays out of the repository (builds/ is ignored).
# Args: [-Config Shipping|Development] [-Out <directory>] [-Test] (run the packaged game's self test afterwards)
param([string]$Config = "Shipping", [string]$Out = "", [switch]$Test)
$repo = Split-Path -Parent $PSScriptRoot
$ue = "E:\Program Files\Epic Games\UE_5.8"
$proj = "$repo\claude_ue5\claude_ue5.uproject"
if (-not $Out) { $Out = "$repo\builds\starship_level" }
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
    $t = $keep -replace '(?m)^GameDefaultMap=.*$', 'GameDefaultMap=/Game/Starship/Maps/starship_level.starship_level'
    $t = $t -replace '(?m)^GlobalDefaultGameMode=.*$', 'GlobalDefaultGameMode=/Script/claude_ue5.SSGameMode'
    if ($t -eq $keep) { "DefaultEngine.ini: no GameDefaultMap / GlobalDefaultGameMode to set"; exit 1 }
    [IO.File]::WriteAllText($ini, $t, $enc)
    & "$ue\Engine\Build\BatchFiles\RunUAT.bat" BuildCookRun "-project=$proj" -noP4 -utf8output -unattended -platform=Win64 "-clientconfig=$Config" `
        -build -nocompileeditor -cook "-map=/Game/Starship/Maps/starship_level" -stage -pak -iostore -compressed -nodebuginfo `
        "-applocaldirectory=$ue\Engine\Binaries\ThirdParty\AppLocalDependencies" -archive "-archivedirectory=$Out"
    $code = $LASTEXITCODE
}
finally { [IO.File]::WriteAllText($ini, $keep, $enc) }
if ($code -ne 0) { "PACKAGE FAILED ($code)"; exit $code }
$exe = "$Out\Windows\claude_ue5.exe"
$size = (Get-ChildItem "$Out\Windows" -Recurse -File | Measure-Object Length -Sum).Sum
"packaged: $exe  ({0:N0} MB in {1} files)" -f ($size / 1MB), (Get-ChildItem "$Out\Windows" -Recurse -File | Measure-Object).Count
if ($Test) {
    # the packaged game flies itself for 12 s without a window and reports
    $to = Join-Path $env:TEMP "claude_ue5_selftest"
    if (Test-Path "$to\selftest.txt") { Remove-Item "$to\selftest.txt" }
    $p = Start-Process -FilePath $exe -ArgumentList "-RenderOffScreen", "-ResX=1280", "-ResY=720", "-SSSelfTest=12", "-SSSelfTestOut=$to" -PassThru
    if (-not $p.WaitForExit(180000)) { $p.Kill(); "SELF TEST: the game did not quit by itself"; exit 1 }
    if (Test-Path "$to\selftest.txt") { "self test ($to):"; Get-Content "$to\selftest.txt" } else { "SELF TEST: no report written"; exit 1 }
}
exit 0
