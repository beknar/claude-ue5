# mistward_castle: record the packaged game's autoplay, one video per hero, into Game Bar's captures folder.
# -Recorder ffmpeg (the default): ffmpeg's desktop duplication (ddagrab) of the primary screen, encoded on the GPU (h264_nvenc,
# else libx264), started only once the game is in front and covers the screen, stopped by ffmpeg itself after the seconds
# (before the game quits): unattended. No sound (ffmpeg here has no loopback capture). -Recorder gamebar: Win+Alt+R as below;
# on 2026-11-01 Game Bar recorded another window (titled "~") in 5 trials of 6 although the game was in front: Game Bar's
# choice of app does not follow a window brought forward by a program.
# For each hero: starts the package (builds\mistward_castle) in windowed fullscreen at the given resolution (the game's own
# settings written for the run: Game Bar recorded the game black in exclusive fullscreen, 832 x 468 at 28 kb/s) with
# -RDStartHero=<hero> -Autoplay=<seconds + 20> (the game plays her and quits after), waits for the castle (-RDMarkFile),
# brings the game to the front and presses Win+Alt+R (Game Bar: start recording), waits the seconds, presses Win+Alt+R again
# (stop), waits for Game Bar's new .mp4 in its captures folder to stop growing and renames it after the hero
# ("Martial Artist.mp4"; an existing name gets " (2)"). The game's own settings are kept and put back.
# Game Bar must be on and allowed to record the game (Settings > Gaming); nobody here watches the videos: the script checks
# each file appeared, grew to its end and how long it is (ffprobe through imageio-ffmpeg when a Python with it is given).
# Args: [-Heroes MartialArtist,Summoner,...] [-Seconds 300] [-Res 3840x2160] [-Game <claude_ue5.exe>] [-Py <python with imageio_ffmpeg>]
param([string[]]$Heroes = @("MartialArtist", "Summoner", "Warrior", "Mage", "Warlock", "Rogue"), [int]$Seconds = 300, [string]$Res = "3840x2160", [int]$Mode = 1,
      [string]$Game = (Join-Path $PSScriptRoot "..\builds\mistward_castle\Windows\claude_ue5.exe"), [string]$Py = "",
      [string]$Recorder = "ffmpeg", [int]$Fps = 60, [string]$Bitrate = "60M", [string]$Suffix = "", [int]$Presses = 3)
$ErrorActionPreference = "Stop"
$Game = (Resolve-Path $Game).Path
$titles = @{ MartialArtist = "Martial Artist" }
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class RDRec {
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr h);
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr c);
    [DllImport("user32.dll")] public static extern bool SetCursorPos(int x, int y);
    [DllImport("user32.dll")] public static extern void mouse_event(uint f, int x, int y, uint d, UIntPtr e);
    public static string RectOf(uint pid) { SetThreadDpiAwarenessContext((IntPtr)(-4)); IntPtr h = WindowOf(pid); RECT r; if (h == IntPtr.Zero || !GetWindowRect(h, out r)) return "none";
        return (r.R - r.L) + "x" + (r.B - r.T) + " at " + r.L + "," + r.T; }
    public delegate bool EnumProc(IntPtr h, IntPtr l);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc f, IntPtr l);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int L, T, R, B; }
    /** the largest visible top-level window of the process */
    public static IntPtr WindowOf(uint pid) {
        IntPtr best = IntPtr.Zero; long area = -1;
        EnumWindows((h, l) => { uint p; GetWindowThreadProcessId(h, out p); RECT r;
            if (p == pid && IsWindowVisible(h) && GetWindowRect(h, out r)) { long a = (long)(r.R - r.L) * (r.B - r.T); if (a > area) { area = a; best = h; } }
            return true; }, IntPtr.Zero);
        return best;
    }
    /** the process's window in front: an Alt tap first (Windows lets the process that had the last input set the foreground), then
     *  checked by the foreground window's process */
    public static bool Front(uint pid) {
        IntPtr h = WindowOf(pid);
        if (h == IntPtr.Zero) return false;
        keybd_event(0x12, 0, 0, UIntPtr.Zero); keybd_event(0x12, 0, 2, UIntPtr.Zero);
        ShowWindow(h, 5); BringWindowToTop(h); SetForegroundWindow(h);
        System.Threading.Thread.Sleep(300);
        // (and a click in its middle with Alt held, as a player's click: Game Bar records the app the user last activated, and
        //  a window only brought forward by a program was not it (two trials of five recorded another window). Autoplay
        //  takes no key held with Alt as the player's)
        SetThreadDpiAwarenessContext((IntPtr)(-4)); RECT r;
        if (GetWindowRect(h, out r)) {
            SetCursorPos((r.L + r.R) / 2, (r.T + r.B) / 2);
            keybd_event(0x12, 0, 0, UIntPtr.Zero);
            mouse_event(0x0002, 0, 0, 0, UIntPtr.Zero); System.Threading.Thread.Sleep(60); mouse_event(0x0004, 0, 0, 0, UIntPtr.Zero);
            keybd_event(0x12, 0, 2, UIntPtr.Zero);
            System.Threading.Thread.Sleep(300);
        }
        uint fp; GetWindowThreadProcessId(GetForegroundWindow(), out fp);
        return fp == pid;
    }
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
# (the game's settings: a Shipping game's in LocalAppData, a Development game's beside it (as package_mistward.ps1); both kept,
#  as byte arrays, and put back)
$gus = @((Join-Path $env:LOCALAPPDATA "claude_ue5\Saved\Config\Windows\GameUserSettings.ini"), (Join-Path (Split-Path $Game) "claude_ue5\Saved\Config\Windows\GameUserSettings.ini"))
$kept = @{}; foreach ($g in $gus) { $kept[$g] = if (Test-Path $g) { , [byte[]][IO.File]::ReadAllBytes($g) } else { $null } }
$bin = (Join-Path (Split-Path $Game) "claude_ue5\Binaries\Win64").ToLower()
function Settings([string]$g) {
    # (the file as it was with the window mode and resolution set: windowed fullscreen (1) at $rx x $ry)
    $want = [ordered]@{ ResolutionSizeX = $rx; ResolutionSizeY = $ry; LastUserConfirmedResolutionSizeX = $rx; LastUserConfirmedResolutionSizeY = $ry;
                        FullscreenMode = $Mode; LastConfirmedFullscreenMode = $Mode; PreferredFullscreenMode = $Mode }
    $txt = if ($null -ne $kept[$g]) { [Text.Encoding]::UTF8.GetString($kept[$g]) } else { "" }
    if ($txt -notmatch '\[/Script/Engine\.GameUserSettings\]') { $txt = "[/Script/Engine.GameUserSettings]`r`n" + $txt }
    foreach ($k in $want.Keys) {
        if ($txt -match "(?m)^$k=") { $txt = [regex]::Replace($txt, "(?m)^$k=.*$", "$k=$($want[$k])") }
        else { $txt = $txt.Replace("[/Script/Engine.GameUserSettings]", "[/Script/Engine.GameUserSettings]`r`n$k=$($want[$k])") }
    }
    return $txt
}
$made = @()
$ff = $null
if ($Recorder -eq "ffmpeg") {
    if (-not $Py) { throw "-Recorder ffmpeg needs -Py (a Python with imageio_ffmpeg: its ffmpeg)" }
    $ff = (& $Py -c "import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())").Trim()
    $enc = (& $ff -hide_banner -encoders 2>$null | Out-String)
    $codec = if ($enc -match 'h264_nvenc') { @("-c:v", "h264_nvenc", "-preset", "p5", "-rc", "vbr", "-b:v", $Bitrate, "-maxrate", $Bitrate) } else { @("-vf", "hwdownload,format=bgra", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20") }
    "recorder: ffmpeg desktop duplication, $Fps fps, $($codec[1])"
}
try {
foreach ($h in $Heroes) {
    if (Test-Path $mark) { Remove-Item $mark -Force }
    $t0 = Get-Date
    # (windowed fullscreen at the resolution, in the settings of both places a packaged game reads them from; put back at the end)
    foreach ($g in $gus) { New-Item -ItemType Directory -Force (Split-Path $g) | Out-Null; [IO.File]::WriteAllText($g, (Settings $g), (New-Object Text.UTF8Encoding $false)) }
    $l = Start-Process -FilePath $Game -ArgumentList @("-RDStartHero=$h", "-Autoplay=$($Seconds + 60)", "-AutoplayLocked", "-RDMarkFile=$mark") -PassThru
    $p = $null
    for ($s = 0; $s -lt 60 -and -not $p; $s++) { Start-Sleep 1; $p = Get-Process "claude_ue5*" -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.ToLower().StartsWith($bin) -and $_.StartTime -ge $t0.AddSeconds(-1) } | Select-Object -First 1 }
    if (-not $p) { "$h : the game did not start"; continue }
    for ($s = 0; $s -lt 180 -and -not (Test-Path $mark) -and -not $p.HasExited; $s++) { Start-Sleep 1 }
    if (-not (Test-Path $mark)) { "$h : the castle never began (no mark)"; Stop-Process -Id $p.Id -Force; continue }
    Start-Sleep 3
    # (the game in front, checked by the foreground window's process; never recorded otherwise: Game Bar records the window in
    #  front, and a trial with the game behind recorded another window)
    $front = $false
    for ($s = 0; $s -lt 12 -and -not $front; $s++) { $front = [RDRec]::Front([uint32]$p.Id); if (-not $front) { Start-Sleep -Milliseconds 500 } }
    if (-not $front) { "$h : the game could not be brought to the front: not recorded"; foreach ($q in @($p, $l)) { if ($q -and -not $q.HasExited) { Stop-Process -Id $q.Id -Force } }; continue }
    Start-Sleep 1
    $rect = [RDRec]::RectOf([uint32]$p.Id)
    $title = $(if ($titles[$h]) { $titles[$h] } else { $h }) + $Suffix
    if ($Recorder -eq "ffmpeg") {
        # (the game must cover the screen: the capture is of the screen)
        if ($rect -ne "$($rx)x$($ry) at 0,0") { "$h : the game's window is $rect, not the screen: not recorded"; foreach ($q in @($p, $l)) { if ($q -and -not $q.HasExited) { Stop-Process -Id $q.Id -Force } }; continue }
        $dst = Join-Path $cap "$title.mp4"; $k = 2
        while (Test-Path $dst) { $dst = Join-Path $cap "$title ($k).mp4"; $k++ }
        $rec0 = Get-Date
        $args_ = @("-hide_banner", "-loglevel", "error", "-init_hw_device", "d3d11va=dx", "-filter_hw_device", "dx", "-f", "lavfi", "-i", "ddagrab=output_idx=0:framerate=$($Fps):draw_mouse=0") + $codec + @("-t", "$Seconds", "-movflags", "+faststart", "`"$dst`"")          # (quoted: Start-Process splits a path at its spaces)
        $fp_ = Start-Process -FilePath $ff -ArgumentList $args_ -PassThru -WindowStyle Hidden -RedirectStandardError (Join-Path $env:TEMP "rd_record_ffmpeg.txt")
        # (in front the whole time: checked every 10 s)
        $still = $true
        while (-not $fp_.HasExited) { Start-Sleep 10; if (-not $fp_.HasExited) { $fpid = 0; [void][RDRec]::GetWindowThreadProcessId([RDRec]::GetForegroundWindow(), [ref]$fpid); if ($fpid -ne $p.Id) { $still = $false } } }
        $rec1 = Get-Date
        $new = if (Test-Path $dst) { Get-Item $dst } else { $null }
        if (-not $new) { "$h : NO VIDEO (ffmpeg: $((Get-Content (Join-Path $env:TEMP 'rd_record_ffmpeg.txt') -Raw)))" }
    }
    else {
    $files0 = @(Get-ChildItem $cap -Filter *.mp4 -ErrorAction SilentlyContinue | ForEach-Object FullName)
    # (Game Bar makes its file as a recording starts: none within 8 s, the press was not taken (2026-11-01: a run's every first
    #  press was ignored and the stop press started a 15 s clip instead); pressed again, three times at most)
    $started = $false
    $pressT = @()
    for ($try = 0; $try -lt $Presses -and -not $started; $try++) {
        $pressT += [int]((Get-Date) - $t0).TotalSeconds
        GameBarRecord
        for ($s = 0; $s -lt 20 -and -not $started; $s++) { Start-Sleep -Milliseconds 500; $started = [bool](Get-ChildItem $cap -Filter *.mp4 -ErrorAction SilentlyContinue | Where-Object { $files0 -notcontains $_.FullName }) }
    }
    "$h : Game Bar presses at $($pressT -join ', ') s after launch; started: $started"
    $rec0 = Get-Date
    if (-not $started) { "$h : Game Bar did not start recording ($Presses presses): not recorded"; foreach ($q in @($p, $l)) { if ($q -and -not $q.HasExited) { Stop-Process -Id $q.Id -Force } }; continue }
    Start-Sleep $Seconds
    $still = [RDRec]::Front([uint32]$p.Id)
    GameBarRecord
    $rec1 = Get-Date
    # (the new file, once it stops growing)
    $new = $null; $last = -1
    for ($s = 0; $s -lt 120; $s++) {
        Start-Sleep 2
        $new = Get-ChildItem $cap -Filter *.mp4 -ErrorAction SilentlyContinue | Where-Object { $files0 -notcontains $_.FullName } | Sort-Object LastWriteTime | Select-Object -Last 1
        # (finished: its size still for 2 s and, with a Python, ffmpeg reads its length (Game Bar writes the index last: a clip
        #  whose size had stopped was not yet readable))
        if ($new -and $new.Length -eq $last -and $new.Length -gt 0) {
            if (-not $Py) { break }
            $ok = & $Py -c "import imageio_ffmpeg, subprocess, re, sys; r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-i', sys.argv[1]], capture_output=True, text=True).stderr; print(1 if re.search(r'Duration: \d', r) else 0)" $new.FullName
            if ("$ok".Trim() -eq "1") { break }
        }
        if ($new) { $last = $new.Length }
    }
    }
    # (the game quits itself 20 s after the recording's time; stopped if it has not)
    for ($s = 0; $s -lt 60 -and -not $p.HasExited; $s++) { Start-Sleep 1 }
    foreach ($q in @($p, $l)) { if ($q -and -not $q.HasExited) { Stop-Process -Id $q.Id -Force -Confirm:$false } }
    if (-not $new) { "$h : NO VIDEO (the game in front: $front)"; continue }
    if ($Recorder -ne "ffmpeg") {
        $dst = Join-Path $cap "$title.mp4"; $k = 2
        while (Test-Path $dst) { $dst = Join-Path $cap "$title ($k).mp4"; $k++ }
        "$h : Game Bar named it '$($new.Name)' (the app it recorded)"
        # (a clip of another app is not kept, and not looked at: it can be a private window)
        if ($new.Name -notlike "claude_ue5*") { Remove-Item $new.FullName -Force; "$h : WRONG APP recorded: the clip was deleted unseen"; continue }
        Rename-Item $new.FullName (Split-Path $dst -Leaf)
    }
    $len = ""
    if ($Py) {
        $len = & $Py -c "import imageio_ffmpeg, subprocess, re, sys; r = subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-i', sys.argv[1]], capture_output=True, text=True).stderr; d = re.search(r'Duration: ([\d:.]+)', r); v = re.search(r'Video: .*?(\d{3,5})x(\d{3,5})', r); print((d.group(1) if d else '?') + ' ' + (v.group(1) + 'x' + v.group(2) if v else '?'))" $dst
    }
    "{0}: {1} ({2:N0} MB{3}) | recorded {4:N0} s | the game in front at the start / the end: {5} / {6} | its window {7}" -f $h, $dst, ((Get-Item $dst).Length / 1MB), ($(if ($len) { ", $len" } else { "" })), ($rec1 - $rec0).TotalSeconds, $front, $still, $rect
    $made += $dst
}
}
finally {
    foreach ($q in Get-Process "claude_ue5*" -ErrorAction SilentlyContinue | Where-Object { $_.Path -and $_.Path.ToLower().StartsWith($bin) }) { Stop-Process -Id $q.Id -Force }
    foreach ($g in $gus) { if ($null -ne $kept[$g]) { [IO.File]::WriteAllBytes($g, $kept[$g]) } elseif (Test-Path $g) { Remove-Item $g -Force } }
    "the game's settings put back as they were"
}
"videos: $($made.Count) of $($Heroes.Count) in $cap"
