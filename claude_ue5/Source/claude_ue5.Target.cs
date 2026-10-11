using UnrealBuildTool;

public class claude_ue5Target : TargetRules
{
	public claude_ue5Target(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("claude_ue5");
	}
}
