using UnrealBuildTool;
public class ChibiContact : ModuleRules
{
    public ChibiContact(ReadOnlyTargetRules target) : base(target)
    {
        PublicDependencyModuleNames.AddRange(new[] { "Core", "CoreUObject", "Engine", "InputCore", "RHI", "AnimationCore" });
    }
}

