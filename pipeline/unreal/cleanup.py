"""Delete obsolete MetaHuman character iterations (keeps v8 as backup and v9)."""
import unreal
eal = unreal.EditorAssetLibrary
dead = []
for a in eal.list_assets("/Game/Fig4/MetaHuman", recursive=False) + eal.list_assets("/Game/Fig4/Try", recursive=False):
    base = a.split(".")[-1]
    if base.startswith(("MHC_Fig4v8", "MHC_Fig4v9")):
        continue
    dead.append(a.split(".")[0])
for d in dead:
    print("delete", d, eal.delete_asset(d))
if eal.does_directory_exist("/Game/Fig4/Try"):
    eal.delete_directory("/Game/Fig4/Try")
print("left:", eal.list_assets("/Game/Fig4/MetaHuman", recursive=False))
