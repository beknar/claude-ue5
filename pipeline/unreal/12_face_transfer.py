"""Export v9's head DNA to disk and fit MHC_Fig4_Final's face to it (body stays parametric).
Args: dna_out_dir"""
import sys, os, glob, unreal
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
mhs = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
print("alignment options:", [m for m in dir(unreal.MetaHumanAlignmentOptions) if m.isupper()])
src = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4v9")
dst = unreal.load_asset("/Game/Fig4/MetaHuman/MHC_Fig4_Final")
if not (mhs.is_object_added_for_editing(src) or mhs.try_add_object_to_edit(src)):
    raise RuntimeError("edit src")
p = unreal.MetaHumanDNAExportParams()
p.external_path = out; p.dna_head = True; p.dna_body = False
try:
    unreal.MetaHumanCharacterExportBlueprintLibrary.export_dna(src, p)
except RuntimeError as e:
    print("(non-fatal)", str(e)[:120])
mhs.remove_object_to_edit(src)
files = glob.glob(os.path.join(out, "**", "*.dna"), recursive=True)
print("dna files:", files)
head = [f for f in files if "head" in os.path.basename(f).lower() or "face" in os.path.basename(f).lower()] or files
if not (mhs.is_object_added_for_editing(dst) or mhs.try_add_object_to_edit(dst)):
    raise RuntimeError("edit dst")
ip = unreal.ImportFromDNAParams()
ip.isolate_head_from_body = True
ip.import_whole_rig = False
ip.alignment_options = unreal.MetaHumanAlignmentOptions.NONE     # keep the conformed position (same 153.7 cm body)
code = mhs.import_from_face_dna(dst, head[0], ip)
print("import code:", code)
unreal.MetaHumanGeneratorSubsystemWrapper.reset_neck_to_body(dst)
unreal.EditorAssetLibrary.save_loaded_asset(dst, only_if_is_dirty=False)
print("FACE transferred from", head[0])
