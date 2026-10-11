using UnrealBuildTool;

public class claude_ue5EditorTarget : TargetRules
{
	public claude_ue5EditorTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Editor;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("claude_ue5");
	}
}
