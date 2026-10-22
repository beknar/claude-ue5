# Build the claude_ue5 C++ module (editor target). Close the editor first.
# UE 5.8's SwarmInterface build rules demand a .NET Framework SDK (NETFXSDK) even though the engine module is
# precompiled; without one installed, point UnrealBuildTool at a stand-in AutoSDK folder for this build only
# (UE_SDKS_ROOT\HostWin64\Win64\Windows Kits\NETFXSDK\4.6.2\Include\um\mscoree.h). Installing the .NET Framework
# 4.8.x Developer Pack makes this unnecessary.
param([string]$Config = "Development")
$repo = Split-Path -Parent $PSScriptRoot
$ue = "E:\Program Files\Epic Games\UE_5.8"
$hasNetFx = Test-Path "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Microsoft SDKs\NETFXSDK\4.6.2"
if (-not $hasNetFx -and -not $env:UE_SDKS_ROOT) {
    $root = Join-Path $env:TEMP "claude_ue5_autosdk"
    $inc = Join-Path $root "HostWin64\Win64\Windows Kits\NETFXSDK\4.6.2\Include\um"
    New-Item -ItemType Directory -Force $inc | Out-Null
    New-Item -ItemType Directory -Force (Join-Path $root "HostWin64\Win64\Windows Kits\NETFXSDK\4.6.2\Lib\um\x64") | Out-Null
    if (-not (Test-Path "$inc\mscoree.h")) { Set-Content -Path "$inc\mscoree.h" -Value "// stand-in for UnrealBuildTool (SwarmInterface rules)" }
    $env:UE_SDKS_ROOT = $root
}
# A Fab plugin installed in the engine without its source (KitBash3D's Cargo: binaries only) stops UnrealBuildTool
# ("Could not find definition for module"). Such plugins are left out of the build; the editor still loads their own
# binaries.
$skip = @()
foreach ($u in Get-ChildItem "$ue\Engine\Plugins\Marketplace" -Recurse -Depth 2 -Filter *.uplugin -ErrorAction SilentlyContinue) {
    if (-not (Test-Path (Join-Path $u.DirectoryName "Source"))) { $skip += "-DisablePlugin=$($u.BaseName)" }
}
& "$ue\Engine\Build\BatchFiles\Build.bat" claude_ue5Editor Win64 $Config "-Project=$repo\claude_ue5\claude_ue5.uproject" -WaitMutex -NoHotReloadFromIDE @skip
exit $LASTEXITCODE
