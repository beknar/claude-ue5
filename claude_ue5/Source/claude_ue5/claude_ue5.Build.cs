using UnrealBuildTool;

public class claude_ue5 : ModuleRules
{
	public claude_ue5(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicIncludePaths.Add(ModuleDirectory);
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine", "InputCore", "ProceduralMeshComponent", "Niagara", "EnhancedInput", "RenderCore", "RHI", "AudioMixer", "SlateCore", "Slate", "HairStrandsCore", "ImageCore" });
		// (tests in the editor: play in a window of its own (RD/RDEditorPlay.cpp); never in a game)
		if (Target.bBuildEditor) PrivateDependencyModuleNames.Add("UnrealEd");
	}
}
