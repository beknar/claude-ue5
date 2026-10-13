"""random_dungeoncombat_level: reads the recording of the game's sound self test (the game started with
-RDSoundTest=<dir> plays one flat sound and the same placed sound at known places round her, records what the audio
device puts out and writes <dir>/soundtest.wav and soundtest.txt; pipeline/unreal/799_rdc_sound_test.ps1 runs it).
For each step: the level of the second after it (200 Hz - 6 kHz, both channels) and how much louder the left channel
is than the right. Checks what counting calls cannot: that a placed sound is in the output at all, that one on her
right is louder in the right channel and one on her left in the left, and that the same sound is quieter the farther
away it is, down to nothing.

Usage (a Python with numpy):  rdc_sound_check.py <dir>      prints "RDCSOUNDCHECK ok" or "... FAILED" with the figures"""
import sys, os, wave
import numpy as np

d = sys.argv[1]
w = wave.open(os.path.join(d, "soundtest.wav"), "rb"); sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
x = np.frombuffer(w.readframes(n), dtype="<i2" if sw == 2 else "<i4").astype(np.float64).reshape(-1, ch) / float(1 << (8 * sw - 1))
log = [l.strip() for l in open(os.path.join(d, "soundtest.txt"), encoding="utf-8-sig") if l.strip()]
steps = [(float(p[0]), p[1].strip()) for p in (l.split("|") for l in log[1:]) if len(p) >= 3 and p[1].strip() != "end"]
print(log[0]); print("%s: %d Hz, %d channels, %.1f s, peak %.1f dBFS" % ("soundtest.wav", sr, ch, n / sr, 20 * np.log10(np.abs(x).max() + 1e-9)))


def band(s):
    """power of 200 Hz - 6 kHz in a mono block"""
    sp = np.abs(np.fft.rfft(s * np.hanning(len(s)))) ** 2; fr = np.fft.rfftfreq(len(s), 1.0 / sr)
    return sp[(fr >= 200) & (fr < 6000)].sum() / len(s) ** 2


def db(p): return 10 * np.log10(p + 1e-15)


quiet = db(band(x[int(0.2 * sr):int(0.9 * sr)].mean(axis=1)))            # (before the first step: the room tone)
res = {}
for t, what in steps:
    s = x[int((t + 0.02) * sr):int((t + 1.2) * sr)]
    res[what] = (db(band(s.mean(axis=1))), db(band(s[:, 0])) - db(band(s[:, -1])))
    print("%5.2f s  %-20s level %6.1f dB (%+5.1f over the room tone)   left - right %+5.1f dB" % (t, what, res[what][0], res[what][0] - quiet, res[what][1]))
lv = lambda k: res[k][0]; lr = lambda k: res[k][1]
checks = {
    "the flat sound is there": max(lv("flat"), lv("flat again")) > quiet + 15,      # (the very first sound of a session can come too late for its second)
    "a placed sound 2 m away is there": lv("2 m ahead of her") > quiet + 15,
    "ahead: both ears alike": abs(lr("2 m ahead of her")) < 3,
    "on her right: the right ear": lr("4 m to her right") < -3,
    "on her left: the left ear": lr("4 m to her left") > 3,
    "12 m: quieter than 2 m": lv("12 m ahead") < lv("2 m ahead of her") - 4,
    "25 m: quieter than 12 m": lv("25 m ahead") < lv("12 m ahead") - 4,
}
if "--mono" in sys.argv:                                                  # (a render: placed sounds are centred)
    for k in ("on her right: the right ear", "on her left: the left ear"): checks.pop(k)
bad = [k for k, v in checks.items() if not v]
print("RDCSOUNDCHECK %s | %s" % ("ok" if not bad else "FAILED", "; ".join("%s: %s" % (k, "yes" if v else "NO") for k, v in checks.items())))
