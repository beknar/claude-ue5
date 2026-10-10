import unreal
for n in ("MetaHumanCharacterEyeMakeupType", "MetaHumanCharacterLipsMakeupType", "MetaHumanCharacterBlushMakeupType",
          "MetaHumanCharacterEyelashesType", "MetaHumanCharacterFrecklesMask", "MetaHumanCharacterSkinPreviewMaterial",
          "MetaHumanRigType", "MetaHumanDefaultPipelineType", "MetaHumanQualityLevel", "MetaHumanCharacterTextureSourceResolution"):
    e = getattr(unreal, n, None)
    if e is None:
        print(n, "missing"); continue
    print(n, [m for m in dir(e) if m.isupper()])
print(unreal.MetaHumanCharacterTextureRequestParams().to_dict() if hasattr(unreal, "MetaHumanCharacterTextureRequestParams") else "")
print(unreal.MetaHumanCharacterAutoRiggingRequestParams().to_dict())
print(unreal.MetaHumanCharacterEditorBuildParameters().to_dict())
