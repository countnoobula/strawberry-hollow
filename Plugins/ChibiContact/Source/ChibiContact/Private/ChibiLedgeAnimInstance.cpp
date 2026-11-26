#include "ChibiLedgeAnimInstance.h"
#include "Animation/AnimInstanceProxy.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimationPoseData.h"
#include "Animation/AnimNodeBase.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/SkeletalMesh.h"
#include "Engine/World.h"
#include "TwoBoneIK.h"
#include "UObject/UnrealType.h"

namespace
{
struct FGrip
{
    TWeakObjectPtr<UPrimitiveComponent> Support;
    FVector LocalPoint, LocalInward, LocalAcross;

    FTransform WorldFrame() const
    {
        const FTransform& T = Support->GetComponentTransform();
        const FVector Forward = T.TransformVector(LocalInward).GetSafeNormal();
        const FVector Normal = Forward.Cross(T.TransformVector(LocalAcross)).GetSafeNormal();
        return FTransform(FRotationMatrix::MakeFromXZ(Forward, Normal).ToQuat(), T.TransformPosition(LocalPoint));
    }
};

struct FArm
{
    int32 Bones[3] = {INDEX_NONE, INDEX_NONE, INDEX_NONE};
    FQuat RestBasis = FQuat::Identity;
    FGrip Grip;
    FGrip FromGrip;
    FVector Wrist = FVector::ZeroVector;
    FQuat Rotation = FQuat::Identity;
    bool bActive = false;
};

// Search across the lip for the first load-bearing top patch. The gameplay
// ledge is a coarse starting point; each hand samples its own triangle.
bool FindGrip(UWorld& World, const AActor& Runner, FVector Edge, FVector Inward, FGrip& Grip)
{
    FCollisionQueryParams Query(SCENE_QUERY_STAT(ChibiPalm), true, &Runner);
    FHitResult Face;
    // The coarse ledge can be well above a beveled rim, especially on
    // a tall instance. Locate the lower wall before scanning for its top.
    UPrimitiveComponent* Support = nullptr;
    for (double Drop : {45., 24., 10.})
    {
        const FVector FaceProbe = Edge - FVector::UpVector * Drop;
        if (World.LineTraceSingleByChannel(Face, FaceProbe - Inward*80, FaceProbe + Inward*45, ECC_Visibility, Query)
            && -Face.ImpactNormal.Dot(Inward) > .35)
        {
            Support = Face.GetComponent();
            break;
        }
    }
    if (!Support) return false;
    FVector Facing = (-Face.ImpactNormal).GetSafeNormal2D();
    if (Facing.Dot(Inward) < .5) Facing = Inward;
    const FVector Start(Face.ImpactPoint.X, Face.ImpactPoint.Y, Edge.Z);
    FHitResult Best;
    bool bFoundTop = false;
    double BestDistance = TNumericLimits<double>::Max();
    int SearchEnd = 48;
    for (int Depth = -4; Depth <= SearchEnd; Depth += 2)
    {
        const FVector Sample = Start + Facing * Depth;
        FHitResult Top;
        if (!Support->LineTraceComponent(Top, Sample + FVector::UpVector*30, Sample - FVector::UpVector*65, Query)
            || Top.ImpactNormal.Z < .58) continue;
        // Prefer the usable patch nearest the detected ledge within a
        // palm-depth band. This avoids choosing a steep lower bevel.
        if (!bFoundTop) SearchEnd = FMath::Min(SearchEnd, Depth + 12);
        bFoundTop = true;
        const double Distance = FVector::DistSquared(Edge, Top.ImpactPoint);
        if (Distance < BestDistance) { Best = Top; BestDistance = Distance; }
    }
    if (!bFoundTop) return false;
    const FVector Tangent = FVector::VectorPlaneProject(Facing, Best.ImpactNormal).GetSafeNormal();
    const FTransform& Transform = Support->GetComponentTransform();
    Grip.Support = Support;
    Grip.LocalPoint = Transform.InverseTransformPosition(Best.ImpactPoint);
    Grip.LocalInward = Transform.InverseTransformVector(Tangent);
    Grip.LocalAcross = Transform.InverseTransformVector(Best.ImpactNormal.Cross(Tangent));
    return true;
}
class FLedgeProxy final : public FAnimInstanceProxy
{
public:
    explicit FLedgeProxy(UAnimInstance* Instance) : FAnimInstanceProxy(Instance) {}

private:
    FArm Arms[2];
    TWeakObjectPtr<UActorComponent> Parkour;
    const FNameProperty* StateProperty = nullptr;
    const FStructProperty* EdgeProperty = nullptr;
    const FStructProperty* NormalProperty = nullptr;
    const FNumericProperty* AlphaProperty = nullptr;
    const FStructProperty* StepStartProperty = nullptr;
    const FStructProperty* StepEndProperty = nullptr;
    const FNumericProperty* StepPhaseProperty = nullptr;
    float PreviousStepPhase = -1;
    float Weight = 0;
    bool bHolding = false;
    UAnimSequence* SurfaceStroke = nullptr;
    UAnimSequence* TreadWater = nullptr;
    float SwimPhase = 0.f, SurfaceWeight = 0.f, TreadWeight = 0.f;
    FName Clip, PreviousClip;
    TArray<FTransform> LastStride;
    TArray<FTransform> StrideOffsets;
    float StridePhase = 0.f;

    static bool IsStride(FName Name)
    {
        return Name == TEXT("AS_Chibi_Run") || Name == TEXT("AS_Chibi_Sprint");
    }

    uint16 StrideBoneSerial = 0;
    int32 Pelvis = INDEX_NONE;
    float FrameSeconds = 0.f;
    float BlendTime = 0.f;

    void Initialize(UAnimInstance* Instance) override
    {
        FAnimInstanceProxy::Initialize(Instance);
        Parkour.Reset();
        LastStride.Reset();
        StrideOffsets.Reset();
        Clip = NAME_None;
        PreviousClip = NAME_None;
        PreviousStepPhase = -1;
        Weight = 0;
        bHolding = false;
        for (FArm& Arm : Arms) Arm = FArm();
        USkeletalMeshComponent* Mesh = Instance->GetSkelMeshComponent();
        if (!Mesh || !Mesh->GetSkeletalMeshAsset()) return;
        const FReferenceSkeleton& Ref = Mesh->GetSkeletalMeshAsset()->GetRefSkeleton();
        Pelvis = Ref.FindBoneIndex(TEXT("pelvis"));
        static const FName Bones[2][3] = {{TEXT("upperarm_l"),TEXT("lowerarm_l"),TEXT("hand_l")},
                                            {TEXT("upperarm_r"),TEXT("lowerarm_r"),TEXT("hand_r")}};
        for (int Side = 0; Side < 2; ++Side)
        {
            FArm& Arm = Arms[Side];
            for (int I=0; I<3; ++I)
            {
                Arm.Bones[I] = Ref.FindBoneIndex(Bones[Side][I]);
                if (Arm.Bones[I] == INDEX_NONE) { Parkour.Reset(); return; }
            }
        }
        for (int Side = 0; Side < 2; ++Side)
        {
            FArm& Arm = Arms[Side];
            const FTransform Hand = Ref.GetBoneAbsoluteTransform(Arm.Bones[2]);
            const FVector Other = Ref.GetBoneAbsoluteTransform(Arms[1-Side].Bones[2]).GetLocation();
            const FVector Out = (Hand.GetLocation() - Other).GetSafeNormal();
            const FVector Fingers = (Out - FVector::UpVector).GetSafeNormal();
            const FVector Back = (Out + FVector::UpVector).GetSafeNormal();
            Arm.RestBasis = Hand.GetRotation().Inverse() * FRotationMatrix::MakeFromXZ(Fingers, Back).ToQuat();
        }
    }

    void BindParkour(UAnimInstance* Instance)
    {
        USkeletalMeshComponent* Mesh = Instance->GetSkelMeshComponent();
        AActor* Owner = Instance->GetOwningActor();
        if (!Owner || !Owner->HasActorBegunPlay()) return;
        for (UActorComponent* C : Owner->GetComponents())
        {
            UClass* Class = C->GetClass();
            StateProperty = FindFProperty<FNameProperty>(Class, TEXT("CurrentParkourState"));
            if (!StateProperty) continue;
            EdgeProperty = FindFProperty<FStructProperty>(Class, TEXT("LedgeEdgePoint"));
            NormalProperty = FindFProperty<FStructProperty>(Class, TEXT("LedgeWallNormal"));
            AlphaProperty = FindFProperty<FNumericProperty>(Class, TEXT("MantleAlpha"));
            StepStartProperty = FindFProperty<FStructProperty>(Class, TEXT("ShimmyStartEdge"));
            StepEndProperty = FindFProperty<FStructProperty>(Class, TEXT("ShimmyEndEdge"));
            StepPhaseProperty = FindFProperty<FNumericProperty>(Class, TEXT("ShimmyPhase"));
            if (EdgeProperty && NormalProperty && AlphaProperty && AlphaProperty->IsFloatingPoint()
                && EdgeProperty->Struct == TBaseStructure<FVector>::Get() && NormalProperty->Struct == EdgeProperty->Struct)
            { Parkour = C; Mesh->AddTickPrerequisiteComponent(C); break; }
        }
    }

    void PreUpdate(UAnimInstance* Instance, float Dt) override
    {
        FAnimInstanceProxy::PreUpdate(Instance, Dt);
        FrameSeconds = Dt;
        auto* Player = Instance->GetSkelMeshComponent()->GetSingleNodeInstance();
        const auto* Asset = Player ? Player->GetAnimationAsset() : nullptr;
        const FName NextClip = Asset ? Asset->GetFName() : NAME_None;
        if (IsStride(NextClip) && Player->GetLength() > SMALL_NUMBER)
        {
            if (NextClip != Clip && IsStride(Clip))
                Player->SetPosition(StridePhase * Player->GetLength(), false);
            StridePhase = Player->GetCurrentTime() / Player->GetLength();
        }
        Clip = NextClip;
        auto* Layer = CastChecked<UChibiLedgeAnimInstance>(Instance);
        SurfaceStroke = Layer->SurfaceStroke;
        SurfaceWeight = Layer->SurfaceStrokeWeight;
        if (Clip == TEXT("AS_Chibi_Swim") && SurfaceStroke && Player->GetLength() > SMALL_NUMBER)
        {
            SwimPhase = Player->GetCurrentTime() / Player->GetLength();
            TreadWater = Layer->TreadWater;
            const AActor* Swimmer = Instance->GetOwningActor();
            const float Speed = Swimmer ? Swimmer->GetVelocity().Size2D() : 0.f;
            const float Target = 1.f - FMath::SmoothStep(10.f, 115.f, Speed);
            TreadWeight = FMath::Lerp(TreadWeight, Target, 1.f - FMath::Exp(-7.f * Dt));
        }
        else
            TreadWeight = 0.f;
        if (!Parkour.IsValid() && Arms[1].Bones[2] != INDEX_NONE) BindParkour(Instance);
        UActorComponent* Component = Parkour.Get();
        if (!Component) { Weight = 0; return; }
        const FName State = StateProperty->GetPropertyValue_InContainer(Component);
        const bool bHang = State == TEXT("LedgeHang");
        const bool bMantle = State == TEXT("MantleUp");
        const bool bShimmy = State == TEXT("LedgeShimmy") && StepPhaseProperty && StepPhaseProperty->IsFloatingPoint()
            && StepStartProperty && StepStartProperty->Struct == EdgeProperty->Struct
            && StepEndProperty && StepEndProperty->Struct == EdgeProperty->Struct;
        const float Phase = AlphaProperty->GetFloatingPointPropertyValue(AlphaProperty->ContainerPtrToValuePtr<void>(Component));
        const bool bOnEdge = bHang || bShimmy;
        if (!bOnEdge && !bMantle)
        {
            Weight = 0;
            bHolding = false;
            PreviousStepPhase = -1;
            for (FArm& Arm : Arms) { Arm.Grip.Support.Reset(); Arm.bActive = false; }
            return;
        }
        AActor* Owner = Component->GetOwner();
        const FVector Inward = (-*NormalProperty->ContainerPtrToValuePtr<FVector>(Component)).GetSafeNormal2D();
        const FVector Edge = *EdgeProperty->ContainerPtrToValuePtr<FVector>(Component);

        const float TargetWeight = bOnEdge ? 1.f : 1.f-FMath::SmoothStep(.50f,.83f,Phase);
        if (!bHolding && bOnEdge)
            for (FArm& Arm : Arms) Arm.Grip.Support.Reset();
        bHolding = bOnEdge;
        Weight = FMath::Min(TargetWeight, Weight + Dt * 14);
        const FVector Across = FVector::UpVector.Cross(Inward);
        const float StepPhase = bShimmy ? StepPhaseProperty->GetFloatingPointPropertyValue(
            StepPhaseProperty->ContainerPtrToValuePtr<void>(Component)) : -1.f;
        const FVector Start = bShimmy ? *StepStartProperty->ContainerPtrToValuePtr<FVector>(Component) : Edge;
        const FVector End = bShimmy ? *StepEndProperty->ContainerPtrToValuePtr<FVector>(Component) : Edge;
        const bool bNewStep = bShimmy && (PreviousStepPhase < 0 || StepPhase < PreviousStepPhase);
        PreviousStepPhase = StepPhase;
        const int LeadHand = (End - Start).Dot(Across) >= 0 ? 1 : 0;
        for (int Side=0; Side<2; ++Side)
        {
            FArm& Arm = Arms[Side];
            const FVector Offset = Across * (Side ? 11. : -11.);
            if (bOnEdge && !Arm.Grip.Support.IsValid() && !Inward.IsNearlyZero())
                FindGrip(*Owner->GetWorld(), *Owner, Start + Offset, Inward, Arm.Grip);

            if (bNewStep)
            {
                Arm.FromGrip = Arm.Grip;
                FGrip Next;
                if (FindGrip(*Owner->GetWorld(), *Owner, End + Offset, Inward, Next))
                    Arm.Grip = Next;
                else if (Arm.Grip.Support.IsValid() &&
                    FMath::Abs((Arm.Grip.WorldFrame().GetLocation() - End - Offset).Dot(Across)) > 15.)
                    Arm.Grip.Support.Reset();
            }
            Arm.bActive = Arm.Grip.Support.IsValid();
            if (!Arm.bActive) continue;
            FTransform Frame = Arm.Grip.WorldFrame();
            if (bShimmy && Arm.FromGrip.Support.IsValid())
            {
                // Match the gameplay step. The leading hand lands before the
                // trailing hand lifts, including when the direction reverses.
                const float Reach = Side == LeadHand ? FMath::SmoothStep(.04f,.46f,StepPhase)
                                                     : FMath::SmoothStep(.52f,.94f,StepPhase);
                const FTransform From = Arm.FromGrip.WorldFrame();
                const double Lift = FMath::Min(2., .18 * FVector::Dist(From.GetLocation(), Frame.GetLocation()));
                const FTransform To = Frame;
                Frame.Blend(From, To, Reach);
                Frame.AddToTranslation(Frame.GetUnitAxis(EAxis::Z) * (4. * Reach * (1. - Reach) * Lift));
            }
            const FVector Forward = Frame.GetUnitAxis(EAxis::X);
            const FVector Normal = Frame.GetUnitAxis(EAxis::Z);
            Arm.Rotation = Frame.GetRotation() * Arm.RestBasis.Inverse();
            // Contact marker on the mitten in bind pose: 3.42 cm along
            // the fingers and 2.78 cm toward the palm from the wrist.
            const double Scale = Instance->GetSkelMeshComponent()->GetComponentScale().GetAbsMax();
            Arm.Wrist = Frame.GetLocation() + (Normal*2.78 - Forward*3.42)*Scale;
        }
    }

    void AddDiveArc(FPoseContext& Output, float Phase) const
    {
        if (Pelvis == INDEX_NONE) return;
        const auto Hip = Output.Pose.GetBoneContainer().MakeCompactPoseIndex(FMeshPoseBoneIndex(Pelvis));
        if (!Hip.IsValid()) return;
        FCSPose<FCompactPose> CS;
        CS.InitPose(Output.Pose);
        const FVector Pivot = CS.GetComponentSpaceTransform(Hip).GetLocation();
        const FTransform& Mesh = GetComponentTransform();
        const FVector Right = Mesh.InverseTransformVectorNoScale(GetActorTransform().GetUnitAxis(EAxis::Y));
        const FVector Forward = Mesh.InverseTransformVectorNoScale(GetActorTransform().GetUnitAxis(EAxis::X));
        const FVector Up = Mesh.InverseTransformVectorNoScale(FVector::UpVector);
        const float Arc = FMath::Square(FMath::Sin(PI * Phase));
        const FQuat Pitch(Right, FMath::DegreesToRadians(34.f * Arc));
        FTransform& Root = Output.Pose[FCompactPoseBoneIndex(0)];
        Root.SetLocation(Pivot + Pitch.RotateVector(Root.GetLocation() - Pivot) + (Forward * 13. + Up * 10.) * Arc);
        Root.SetRotation(Pitch * Root.GetRotation());
    }

    bool Evaluate(FPoseContext& Output) override
    {
        const bool bStride = IsStride(Clip);
        const bool bDive = Clip == TEXT("AS_Chibi_Slide");
        const bool bFromStride = IsStride(PreviousClip);
        const bool bSwitchGait = bStride && bFromStride && Clip != PreviousClip;
        if (Clip != PreviousClip)
        {
            StrideOffsets.Reset();
            if (!bFromStride) LastStride.Reset();
            BlendTime = 0.f;
            PreviousClip = Clip;
        }
        if (Clip == TEXT("AS_Chibi_Swim") && SurfaceStroke && SurfaceWeight > ZERO_ANIMWEIGHT_THRESH)
        {
            EvaluateAnimationNode(Output);
            FPoseContext Surface(Output);
            FAnimationPoseData SurfaceData(Surface);
            SurfaceStroke->GetAnimationPose(SurfaceData, FAnimExtractContext(double(SwimPhase * SurfaceStroke->GetPlayLength()), false));
            if (TreadWater && TreadWeight > ZERO_ANIMWEIGHT_THRESH)
            {
                FPoseContext Tread(Output);
                FAnimationPoseData TreadData(Tread);
                TreadWater->GetAnimationPose(TreadData, FAnimExtractContext(double(SwimPhase * TreadWater->GetPlayLength()), false));
                for (const FCompactPoseBoneIndex Bone : Surface.Pose.ForEachBoneIndex())
                    Surface.Pose[Bone].BlendWith(Tread.Pose[Bone], TreadWeight);
            }
            for (const FCompactPoseBoneIndex Bone : Output.Pose.ForEachBoneIndex())
                Output.Pose[Bone].BlendWith(Surface.Pose[Bone], SurfaceWeight);
            return true;
        }
        if (bStride)
        {
            EvaluateAnimationNode(Output);
            const int32 Count = Output.Pose.GetNumBones();
            if (StrideBoneSerial != Output.Pose.GetBoneContainer().GetSerialNumber()) StrideOffsets.Reset();
            if (bSwitchGait && LastStride.Num() == Count && StrideBoneSerial == Output.Pose.GetBoneContainer().GetSerialNumber())
            {
                // Fade the pose difference while the incoming stride keeps cycling.
                StrideOffsets.SetNumUninitialized(Count);
                for (FCompactPoseBoneIndex Bone : Output.Pose.ForEachBoneIndex())
                {
                    const FTransform& Source = LastStride[Bone.GetInt()];
                    const FTransform& Target = Output.Pose[Bone];
                    StrideOffsets[Bone.GetInt()] = FTransform(Source.GetRotation() * Target.GetRotation().Inverse(),
                        Source.GetLocation() - Target.GetLocation(), Source.GetScale3D() - Target.GetScale3D());
                }
            }
            if (StrideOffsets.Num() == Count)
            {
                constexpr float Duration = .20f;
                const float Remaining = 1.f - FMath::SmoothStep(0.f, Duration, BlendTime);
                for (FCompactPoseBoneIndex Bone : Output.Pose.ForEachBoneIndex())
                {
                    const FTransform& Offset = StrideOffsets[Bone.GetInt()];
                    FTransform& Pose = Output.Pose[Bone];
                    Pose.SetRotation(FQuat::Slerp(FQuat::Identity, Offset.GetRotation(), Remaining) * Pose.GetRotation());
                    Pose.AddToTranslation(Offset.GetLocation() * Remaining);
                    Pose.SetScale3D(Pose.GetScale3D() + Offset.GetScale3D() * Remaining);
                }
                BlendTime += FrameSeconds;
                if (BlendTime >= Duration) StrideOffsets.Reset();
            }
            LastStride.SetNumUninitialized(Count);
            StrideBoneSerial = Output.Pose.GetBoneContainer().GetSerialNumber();
            for (FCompactPoseBoneIndex Bone : Output.Pose.ForEachBoneIndex())
                LastStride[Bone.GetInt()] = Output.Pose[Bone];
            return true;
        }
        if ((bDive || Clip == TEXT("AS_Chibi_Idle")) && !LastStride.IsEmpty()
            && LastStride.Num() == Output.Pose.GetNumBones() && StrideBoneSerial == Output.Pose.GetBoneContainer().GetSerialNumber())
        {
            EvaluateAnimationNode(Output);
            const float Duration = bDive ? .38f : .26f;
            const float Phase = FMath::Clamp(BlendTime / Duration, 0.f, 1.f);
            const float Alpha = FMath::SmoothStep(0.f, 1.f, Phase);
            for (FCompactPoseBoneIndex Bone : Output.Pose.ForEachBoneIndex())
            {
                const FTransform Target = Output.Pose[Bone];
                Output.Pose[Bone].Blend(LastStride[Bone.GetInt()], Target, Alpha);
            }
            if (bDive) AddDiveArc(Output, Phase);
            BlendTime += FrameSeconds;
            if (BlendTime >= Duration) LastStride.Reset();
            return true;
        }
        LastStride.Reset();
        if (Weight <= 0 || (!Arms[0].bActive && !Arms[1].bActive)) return false;
        EvaluateAnimationNode(Output); // Linked input supplies the current hang or mantle pose.
        FCSPose<FCompactPose> CS;
        CS.InitPose(Output.Pose);
        const FBoneContainer& Bones = Output.Pose.GetBoneContainer();
        const FTransform& ToWorld = GetComponentTransform();
        FCompactPoseBoneIndex Id[2][3];
        FTransform Chain[2][3];
        FVector BodyShift = FVector::ZeroVector;
        double ArmReach[2] = {};
        for (int Side=0; Side<2; ++Side)
        {
            if (!Arms[Side].bActive) continue;
            for (int I=0; I<3; ++I)
            {
                Id[Side][I] = Bones.MakeCompactPoseIndex(FMeshPoseBoneIndex(Arms[Side].Bones[I]));
                if (!Id[Side][I].IsValid()) return true;
                Chain[Side][I] = CS.GetComponentSpaceTransform(Id[Side][I]) * ToWorld;
            }
            const FTransform* T = Chain[Side];
            const double Length = FVector::Dist(T[0].GetLocation(),T[1].GetLocation()) + FVector::Dist(T[1].GetLocation(),T[2].GetLocation());
            ArmReach[Side] = .95 * Length;
        }
        // Project the chest into both arms' reach. Averaging the two
        // corrections leaves the farther hand hovering on rounded corners.
        for (int Pass=0; Pass<3; ++Pass)
        {
            for (int Side=0; Side<2; ++Side)
            {
                if (!Arms[Side].bActive) continue;
                const FVector Reach = Arms[Side].Wrist - Chain[Side][0].GetLocation() - BodyShift;
                BodyShift += Reach.GetSafeNormal() * FMath::Max(0., Reach.Size() - ArmReach[Side]);
            }
        }
        // Bound visual root travel to the scale of the character. A tall
        // bevel can put the coarse mantle path a torso-length above the lip.
        BodyShift = BodyShift.GetClampedToMaxSize(3.5 * FMath::Max(ArmReach[0], ArmReach[1])) * Weight;
        Output.Pose[FCompactPoseBoneIndex(0)].AddToTranslation(ToWorld.InverseTransformVector(BodyShift));
        for (int Side=0; Side<2; ++Side)
        {
            if (!Arms[Side].bActive) continue;
            FTransform* T = Chain[Side];
            FTransform Parent = CS.GetComponentSpaceTransform(Output.Pose.GetParentBoneIndex(Id[Side][0])) * ToWorld;
            Parent.AddToTranslation(BodyShift);
            for (int I=0; I<3; ++I) T[I].AddToTranslation(BodyShift);
            const FVector Wrist = FMath::Lerp(T[2].GetLocation(), Arms[Side].Wrist, Weight);
            const FVector Pole = T[1].GetLocation() + GetActorTransform().TransformVectorNoScale(FVector(-10,Side ? 13 : -13,-9));
            const FQuat HandRotation = FQuat::Slerp(T[2].GetRotation(),Arms[Side].Rotation,Weight);
            AnimationCore::SolveTwoBoneIK(T[0],T[1],T[2],Pole,Wrist,false,1.,1.);
            T[2].SetRotation(HandRotation);
            for (int I=0; I<3; ++I)
                Output.Pose[Id[Side][I]] = T[I].GetRelativeTransform(I ? T[I-1] : Parent);
        }
        return true;
    }
};
}

FAnimInstanceProxy* UChibiLedgeAnimInstance::CreateAnimInstanceProxy() { return new FLedgeProxy(this); }
void UChibiLedgeAnimInstance::DestroyAnimInstanceProxy(FAnimInstanceProxy* Proxy) { delete static_cast<FLedgeProxy*>(Proxy); }
