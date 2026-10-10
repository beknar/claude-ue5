import unreal
for root in ("/Game/MetaHumans/Fig4",):
    al = unreal.EditorAssetLibrary.list_assets(root, recursive=True)
    print(root, len(al))
    for a in al:
        print(" ", a)
print("Common:", len(unreal.EditorAssetLibrary.list_assets("/Game/MetaHumans/Common", recursive=True)))
