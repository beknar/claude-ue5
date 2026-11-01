# mistward_castle: record the packaged game's autoplay with Windows Game Bar, one video per hero.
# For each hero: starts the package (builds\mistward_castle) in exclusive fullscreen at the given resolution with
# -RDStartHero=<hero> -Autoplay=<seconds + 20> (the game plays her and quits after), waits for the castle (-RDMarkFile),
# brings the game to the front and presses Win+Alt+R (Game Bar: start recording), waits the seconds, presses Win+Alt+R again
# (stop), waits for Game Bar's new .mp4 in its captures folder to stop growing and renames it after the hero
# ("Martial Artist.mp4"; an existing name gets " (2)"). The game's own settings are kept and put back.
# Game Bar must be on and allowed to record the game (Settings > Gaming); nobody here watches the videos: the script checks
# each file appeared, grew to its end and how long it is (ffprobe through imageio-ffmpeg when a Python with it is given).
# Args: [-Heroes MartialArtist,Summoner,...] [-Seconds 300] [-Res 3840x2160] [-Game <claude_ue5.exe>] [-Py <python with imageio_ffmpeg>]
param([string[]]$Heroes = @("MartialArtist", "Summoner", "Warrior", "Mage", "Warlock", "Rogue"), [int]$Seconds = 300, [string]$Res = "3840x2160",
      [string]$Game = (Join-Path $PSScriptRoot "..\builds\mistward_castle\Windows\claude_ue5.exe"), [string]$Py = "")
$ErrorActionPreference = "Stop"
$Game = (Resolve-Path $Game).Path
$titles = @{ MartialArtist = "Martial Artist" }
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class RDRec {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    public static void Combo(byte[] keys) {
        foreach (var k in keys) keybd_event(k, 0, 0, UIntPtr.Zero);
        System.Threading.Thread.Sleep(80);
        for (int i = keys.Length - 1; i >= 0; i--) keybd_event(keys[i], 0, 2, UIntPtr.Zero);
    }
}
'@
function GameBarRecord { [RDRec]::Combo([byte[]](0x5B, 0x12, 0x52)) }          # (Win, Alt, R)
# (Game Bar's captures folder: the Captures shell folder, else Videos\Captures)
$cap = $null
try { $cap = [Environment]::ExpandEnvironmentVariables((Get-ItemProperty "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")."{EDC0FE71-98D8-4F4A-B920-C8DC133CB165}") } catch {}
if (-not $cap) { $cap = Join-Path ([Environment]::GetFolderPath("MyVideos")) "Captures" }
"Game Bar's captures folder: $cap"
$rx, $ry = $Res.Split("x")
$mark = Join-Path $env:TEMP "rd_record_mark.txt"
$gus = Join-Path $env:LOCALAPPDATA "claude_ue5\Saved\Config\Windows\GameUserSettings.ini"
$kept = if (Test-Path $gus) { , [byte[]][IO.File]::ReadAllBytes($gus) } else { $null }
$bin = (Join-Path (Split-Path $Game) "claude_ue5\Binaries\Win64").ToLower()
$made = @()
try {
foreach ($h in $Heroes) {
    if (Test-Path $mark) { Remove-Item $mark -Force }
    $t0 = Get-Date
    $l = Start-Process -FilePath $Game -ArgumentList @("-RDStartHero=$h", "-Autoplay=$($Seconds + 20)", "-RDMarkFile=$mark", "-ResX=$rx", "-ResY=$ry", "-fullscreen") -PassThru
    $p = $null
    for ($s = 0; $s -lt 60 -and -not $p; $s++) { Start-Sleep 1; $p = Get-Process "claude_ue5*" -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.ToLower().StartsWith($bin) -and $_.StartTime -ge $t0.AddSeconds(-1) } | Select-Object -First 1 }
    if (-not $p) { "$h : the game did not start"; continue }
    for ($s = 0; $s -lt 180 -and -not (Test-Path $mark) -and -not $p.HasExited; $s++) { Start-Sleep 1 }
    if (-not (Test-Path $mark)) { "$h : the castle never began (no mark)"; Stop-Process -Id $p.Id -Force; continue }
    Start-Sleep 3
    $p.Refresh(); [void][RDRec]::SetForegroundWindow($p.MainWindowHandle); Start-Sleep 1
    $front = [RDRec]::GetForegroundWindow() -eq $p.MainWindowHandle
    $files0 = @(Get-ChildItem $cap -Filter *.mp4 -ErrorAction SilentlyContinue | ForEach-Object FullName)
    $rec0 = Get-Date
    GameBarRecord
    Start-Sleep $Seconds
    $p.Refresh(); [void][RDRec]::SetForegroundWindow($p.MainWindowHandle); Start-Sleep 0.3
    GameBarRecord
    $rec1 = Get-Date
    # (the new file, once it stops growing)
    $new = $null; $last = -1
    for ($s = 0; $s -lt 120; $s++) {
        Start-Sleep 2
        $new = Get-ChildItem $cap -Filter *.mp4 -ErrorAction SilentlyContinue | Where-Object { $files0 -notcontains $_.FullName } | Sort-Object LastWriteTime | Select-Object -Last 1
        if ($new -and $new.Length -eq $last -and $new.Length -gt 0) { break }
        if ($new) { $last = $new.Length }
    }
    # (the game quits itself 20 s after the recording's time; stopped if it has not)
    for ($s = 0; $s -lt 60 -and -not $p.HasExited; $s++) { Start-Sleep 1 }
    foreach ($q in @($p, $l)) { if ($q -and -not $q.HasExited) { Stop-Process -Id $q.Id -Force -Confirm:$false } }
    $where = (Get-Content $mark -Raw).Trim()
    if (-not $new) { "$h : NO VIDEO (Game Bar made no file; the game in front: $front; $where)"; continue }
    $title = if ($titles[$h]) { $titles[$h] } else { $h }
    $dst = Join-Path $cap "$title.mp4"; $k = 2
    while (Test-Path $dst) { $dst = Join-Path $cap "$title ($k).mp4"; $k++ }
    Rename-Item $new.FullName (Split-Path $dst -Leaf)
    $len = ""
    if ($Py) {
        $len = & $Py -c "import imageio_ffmpeg, subprocess, re, sys; r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-i', sys.argv[1]], capture_output=True, text=True).stderr; d = re.search(r'Duration: ([\d:.]+)', r); v = re.search(r'Video: .*?(\d{3,5})x(\d{3,5})', r); print((d.group(1) if d else '?') + ' ' + (v.group(1) + 'x' + v.group(2) if v else '?'))" $dst
    }
    "{0}: {1} ({2:N0} MB{3}) | recorded {4:N0} s | the game in front: {5} | {6}" -f $h, $dst, ((Get-Item $dst).Length / 1MB), ($(if ($len) { ", $len" } else { "" })), ($rec1 - $rec0).TotalSeconds, $front, $where
    $made += $dst
}
}
finally {
    foreach ($q in Get-Process "claude_ue5*" -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.ToLower().StartsWith($bin) }) { Stop-Process -Id $q.Id -Force }
    if ($null -ne $kept) { [IO.File]::WriteAllBytes($gus, $kept) } elseif (Test-Path $gus) { Remove-Item $gus -Force }
    "the game's settings put back as they were"
}
"videos: $($made.Count) of $($Heroes.Count) in $cap"
