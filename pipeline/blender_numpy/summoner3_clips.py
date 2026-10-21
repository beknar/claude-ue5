"""Summoner3's clips (tripo_build.py's clip maker): her GLB's own Walk and Run are kept; her Idle, the three casts, the
Flinch and the Death are the Mage's, retargeted onto her rig as summoner_clips.py does for the first Summoner (her rig has
the mannequin's bone names already: the bones that rig has and hers lacks, a fourth spine bone, the palms, are skipped there).
Run 832 first (the Mage's flinch and death as FBX)."""
import os, importlib.util
_spec = importlib.util.spec_from_file_location("summoner_clips", os.path.join(os.path.dirname(os.path.abspath(__file__)), "summoner_clips.py"))
_sc = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_sc)


def make_clips(arm, scene, clips):
    made = _sc.make_clips(arm, scene, clips)
    keep_own = [k for k in ("Walk", "Run") if k in clips]
    out = {k: v for k, v in made.items() if k not in keep_own}
    print("SUMMONER3 clips: her own", keep_own, "| the Mage's", sorted(out))
    return out
