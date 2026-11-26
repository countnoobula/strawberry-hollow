#include "ChibiPool.h"
#include "ChibiLedgeAnimInstance.h"
#include "Animation/AnimSequence.h"
#include "Animation/AnimSingleNodeInstance.h"
#include "Components/CapsuleComponent.h"
#include "Components/InstancedStaticMeshComponent.h"
#include "Components/PostProcessComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/SpringArmComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Materials/MaterialInterface.h"
#include "UObject/ConstructorHelpers.h"
#include "UObject/UnrealType.h"
#include "UObject/StructOnScope.h"

namespace
{
constexpr float WaterZ = 145.f, PoolWidth = 720.f, PoolLength = 1920.f, SlopeLength = 1420.f, PoolDepth = 235.f;
float FloorDepth(double X) { return PoolDepth * FMath::Clamp(X / SlopeLength, 0., 1.); }
FNameProperty* StateField(UActorComponent* C)
{
    return C ? FindFProperty<FNameProperty>(C->GetClass(), TEXT("CurrentParkourState")) : nullptr;
}
}

AChibiPool::AChibiPool()
{
    PrimaryActorTick.bCanEverTick = true;
    SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Pool")));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Cube(TEXT("/Engine/BasicShapes/Cube"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Plane(TEXT("/Engine/BasicShapes/Plane"));
    static ConstructorHelpers::FObjectFinder<UStaticMesh> Sphere(TEXT("/Engine/BasicShapes/Sphere"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Tile(TEXT("/Game/Parkour/Environment/Pool/M_PoolTile"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Water(TEXT("/Game/Parkour/Environment/Pool/M_PoolSurface"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> RingMat(TEXT("/Game/Parkour/Environment/Pool/M_PoolRing"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> BubbleMat(TEXT("/Game/Parkour/Environment/Pool/M_PoolBubble"));
    static ConstructorHelpers::FObjectFinder<UMaterialInterface> Filter(TEXT("/Game/Parkour/Environment/Pool/M_PoolUnderwater"));
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Stroke(TEXT("/Game/Characters/ChibiRunner/Animations/AS_Chibi_Swim"));
    SwimClip = Stroke.Object;
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Surface(TEXT("/Game/Characters/ChibiRunner/Animations/AS_Chibi_SurfaceSwim"));
    SurfaceClip = Surface.Object;
    static ConstructorHelpers::FObjectFinder<UAnimSequence> Tread(TEXT("/Game/Characters/ChibiRunner/Animations/AS_Chibi_TreadWater"));
    TreadClip = Tread.Object;

    auto Slab = [&](FName Name, FVector Center, FVector Size, float Pitch=0.f){
        auto* Mesh = CreateDefaultSubobject<UStaticMeshComponent>(Name);
        Mesh->SetupAttachment(RootComponent);
        Mesh->SetStaticMesh(Cube.Object);
        Mesh->SetMaterial(0,Tile.Object);
        Mesh->SetRelativeLocationAndRotation(Center, FRotator(Pitch,0,0));
        Mesh->SetRelativeScale3D(Size/100.);
        return Mesh;
    };
    auto Ramp = [&](FName Name, float X0, float Z0, float X1, float Z1){
        const float Pitch = FMath::RadiansToDegrees(FMath::Atan2(Z1-Z0,X1-X0));
        FVector Center((X0+X1)*.5,0,(Z0+Z1)*.5);
        Center -= FRotator(Pitch,0,0).RotateVector(FVector(0,0,8));
        Slab(Name,Center,FVector(FVector2D(X1-X0,Z1-Z0).Size(),PoolWidth,16),Pitch);
    };
    Ramp(TEXT("Approach"),-720,0,0,WaterZ);
    Ramp(TEXT("Beach"),0,WaterZ,SlopeLength,WaterZ-PoolDepth);
    Ramp(TEXT("DeepFloor"),SlopeLength,WaterZ-PoolDepth,PoolLength,WaterZ-PoolDepth);
    // The standard mantle lands 44 cm behind the lip. Provide a walkable deck.
    constexpr float CopingWidth=100.f;
    for (int Side : {-1,1})
        Slab(Side<0 ? TEXT("LeftCoping") : TEXT("RightCoping"),FVector(PoolLength*.5,Side*(PoolWidth+CopingWidth)*.5,WaterZ-PoolDepth*.5),FVector(PoolLength,CopingWidth,PoolDepth+16));
    Slab(TEXT("EndCoping"),FVector(PoolLength+CopingWidth*.5,0,WaterZ-PoolDepth*.5),FVector(CopingWidth,PoolWidth+2*CopingWidth,PoolDepth+16));

    auto* Sheet = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("WaterSurface"));
    Sheet->SetupAttachment(RootComponent); Sheet->SetStaticMesh(Plane.Object); Sheet->SetMaterial(0,Water.Object);
    Sheet->SetRelativeLocation(FVector(PoolLength*.5,0,WaterZ)); Sheet->SetRelativeScale3D(FVector(PoolLength/100.,PoolWidth/100.,1));
    Sheet->SetCollisionEnabled(ECollisionEnabled::NoCollision); Sheet->SetCastShadow(false);
    auto Effects = [&](FName Name,UStaticMesh* Shape, UMaterialInterface* Mat){
        auto* Mesh = CreateDefaultSubobject<UInstancedStaticMeshComponent>(Name);
        Mesh->SetupAttachment(RootComponent); Mesh->SetStaticMesh(Shape); Mesh->SetMaterial(0,Mat);
        Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision); Mesh->SetGenerateOverlapEvents(false);
        Mesh->SetCastShadow(false); Mesh->SetCanEverAffectNavigation(false);
        return Mesh;
    };
    Rings = Effects(TEXT("SurfaceRipples"),Plane.Object,RingMat.Object); Rings->NumCustomDataFloats=1;
    Bubbles = Effects(TEXT("SwimBubbles"),Sphere.Object,BubbleMat.Object);
    Underwater = CreateDefaultSubobject<UPostProcessComponent>(TEXT("UnderwaterView"));
    Underwater->SetupAttachment(RootComponent); Underwater->bUnbound=true; Underwater->Priority=50;
    Underwater->BlendWeight=0;
    if (Filter.Object) Underwater->Settings.AddBlendable(Filter.Object,1.f);
}

void AChibiPool::EnterWater(ACharacter& Character)
{
    Occupant=&Character;
    OldWalkSpeed=Character.GetCharacterMovement()->MaxWalkSpeed;
    CameraArm=Character.FindComponentByClass<USpringArmComponent>();
    CameraOffset=0; RippleClock=0; Foot=INDEX_NONE;
    for (auto* Component : Character.GetComponents())
        if (StateField(Component)){Parkour=Component;AddTickPrerequisiteComponent(Component);break;}
    Character.GetCharacterMovement()->AddTickPrerequisiteActor(this);
}

void AChibiPool::BeginSwimming()
{
    ACharacter* P=Occupant.Get();
    auto* M=P->GetCharacterMovement();
    auto* Component=Parkour.Get();
    if (auto* State=StateField(Component)){
        OldState=State->GetPropertyValue_InContainer(Component);
        if (OldState!=TEXT("Locomotion")) return;
        State->SetPropertyValue_InContainer(Component,TEXT("PoolSwim"));
        bParkourTick=Component->IsComponentTickEnabled(); Component->SetComponentTickEnabled(false);
    }
    if (auto* Anim=P->GetMesh()->GetSingleNodeInstance()){
        PriorClip=Anim->GetCurrentAsset(); OldClipRate=Anim->GetPlayRate();
        OldClipTime=Anim->GetCurrentTime(); bOldLoop=Anim->IsLooping();
        if (SwimClip) P->GetMesh()->PlayAnimation(SwimClip,true);
    }
    SwimMeshRest=P->GetMesh()->GetRelativeTransform(); SwimPitch=0.f;
    OldFlySpeed=M->MaxFlySpeed; bOldOrient=M->bOrientRotationToMovement;
    M->StopMovementImmediately(); M->SetMovementMode(MOVE_Flying);
    M->MaxFlySpeed=230; M->bOrientRotationToMovement=false;
    bSurfaceSwimming = GetActorTransform().InverseTransformPosition(P->GetActorLocation()).Z > WaterZ - 55.f;
    SurfaceWeight = bSurfaceSwimming ? 1.f : 0.f;
    DiveKickTime = 0.f; BubbleClock=0; bSwimming=true;
}

void AChibiPool::EndSwimming()
{
    if (!bSwimming) return;
    if (auto* P=Occupant.Get()){
        P->GetMesh()->SetRelativeTransform(SwimMeshRest);
        auto* M=P->GetCharacterMovement();
        M->MaxFlySpeed=OldFlySpeed; M->bOrientRotationToMovement=bOldOrient;
        M->SetMovementMode(MOVE_Falling);
        if (auto* Anim=P->GetMesh()->GetSingleNodeInstance(); Anim && PriorClip){
            Anim->SetAnimationAsset(PriorClip,bOldLoop,OldClipRate);
            Anim->SetPosition(OldClipTime,false); Anim->SetPlaying(true);
        }
    }
    if (auto* Component=Parkour.Get()){
        if(auto* State=StateField(Component)) State->SetPropertyValue_InContainer(Component,OldState);
        Component->SetComponentTickEnabled(bParkourTick);
    }
    PriorClip=nullptr; bSwimming=false;
}

void AChibiPool::LeaveWater()
{
    EndSwimming();
    if(auto* P=Occupant.Get()){
        P->GetCharacterMovement()->MaxWalkSpeed=OldWalkSpeed;
        P->GetCharacterMovement()->RemoveTickPrerequisiteActor(this);
    }
    if (auto* C=Parkour.Get()) RemoveTickPrerequisiteComponent(C);
    if (auto* Arm=CameraArm.Get()) Arm->TargetOffset.Z-=CameraOffset;
    CameraOffset=0; CameraArm.Reset(); Parkour.Reset(); Occupant.Reset();
}

bool AChibiPool::TryClimbOut()
{
    auto* C=Parkour.Get();
    auto* State=StateField(C);
    if (!State) return false;
    auto* Grab=C->FindFunction(TEXT("TryGrabLedge"));
    auto* Mantle=C->FindFunction(TEXT("StartLedgeMantle"));
    if (!Grab || !Mantle) return false;

    // Let the same wall, top, facing and reach checks used on cliff shelves
    // decide whether a swimmer can catch this lip.
    FStructOnScope Params(Grab);
    State->SetPropertyValue_InContainer(C,OldState);
    C->ProcessEvent(Grab,Params.GetStructMemory());
    if (State->GetPropertyValue_InContainer(C)!=TEXT("LedgeHang")){
        State->SetPropertyValue_InContainer(C,TEXT("PoolSwim"));
        return false;
    }

    Occupant->GetMesh()->SetRelativeTransform(SwimMeshRest);
    C->SetComponentTickEnabled(bParkourTick);
    bSwimming=false;
    PriorClip=nullptr;
    C->ProcessEvent(Mantle,nullptr);
    return true;
}

void AChibiPool::Swim(float Dt,float Height)
{
    auto* P=Occupant.Get(); auto* PC=Cast<APlayerController>(P->GetController());
    if (!PC) return;

    auto Down=[&](FKey K){return PC->IsInputKeyDown(K) ? 1.f : 0.f;};
    const double X=Down(EKeys::D)-Down(EKeys::A)+PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftX);
    const double Y=Down(EKeys::W)-Down(EKeys::S)+PC->GetInputAnalogKeyState(EKeys::Gamepad_LeftY);
    const FRotator View=PC->GetControlRotation();
    const FRotationMatrix Yaw(FRotator(0,View.Yaw,0));
    FVector Input=Yaw.GetUnitAxis(EAxis::X)*Y + Yaw.GetUnitAxis(EAxis::Y)*X;
    const bool bRise = Down(EKeys::SpaceBar) || Down(EKeys::Gamepad_FaceButton_Bottom);
    const bool bDive = Down(EKeys::C) || Down(EKeys::LeftControl) || Down(EKeys::RightControl) || Down(EKeys::Gamepad_FaceButton_Right);
    const float SurfaceHeight = WaterZ - 4.f;
    if (bDive && !bRise && bSurfaceSwimming)
    {
        bSurfaceSwimming = false;
        DiveKickTime = .32f;
    }
    if (bRise)
    {
        DiveKickTime = 0.f;
        if (Height >= SurfaceHeight - 16.f) bSurfaceSwimming = true;
    }
    DiveKickTime = FMath::Max(0.f, DiveKickTime - Dt);
    auto* M=P->GetCharacterMovement();
    if (bSurfaceSwimming && Input.SizeSquared2D() < .0025f)
    {
        const float Drag = FMath::Exp(-5.f * Dt);
        M->Velocity.X *= Drag;
        M->Velocity.Y *= Drag;
    }
    // Set depth velocity independently of camera pitch and horizontal input.
    float VerticalSpeed = bRise ? 165.f : (bDive || DiveKickTime > 0.f ? -165.f : 0.f);
    if (bSurfaceSwimming || bRise)
        VerticalSpeed = FMath::Min(bSurfaceSwimming ? 165.f : VerticalSpeed, (SurfaceHeight - Height) * 6.f);
    M->Velocity.Z = FMath::FInterpTo(M->Velocity.Z, VerticalSpeed, Dt, 9.f);
    // Flying movement brakes an unpowered axis. Feed its requested direction
    // as well so ascent and descent keep working from a stationary tread.
    Input.Z = FMath::Clamp(VerticalSpeed / 165.f, -1.f, 1.f);
    SurfaceWeight = FMath::FInterpTo(SurfaceWeight, bSurfaceSwimming ? 1.f : 0.f, Dt, 5.f);
    if (auto* Layer = Cast<UChibiLedgeAnimInstance>(P->GetMesh()->GetPostProcessInstance()))
    {
        Layer->SurfaceStroke = SurfaceClip;
        Layer->TreadWater = TreadClip;
        Layer->SurfaceStrokeWeight = SurfaceWeight;
    }
    P->ConsumeMovementInputVector(); P->AddMovementInput(Input.GetClampedToMaxSize(1.),1,true);
    if (Input.SizeSquared2D()>.02)
        P->SetActorRotation(FMath::RInterpTo(P->GetActorRotation(),FRotator(0,Input.Rotation().Yaw,0),Dt,7.f));
    if (bRise && TryClimbOut()) return;
    // Pitch the stroke about the torso while the capsule stays upright for collision.
    const FVector Velocity=M->Velocity;
    const float DesiredPitch=FMath::Clamp(FMath::RadiansToDegrees(FMath::Atan2(Velocity.Z,FMath::Max(42.,Velocity.Size2D()))),-65.,55.);
    SwimPitch=FMath::FInterpTo(SwimPitch,DesiredPitch*(1.f-SurfaceWeight),Dt,5.f);
    const FQuat Tilt=FRotator(SwimPitch,0,0).Quaternion();
    const FVector Pivot(0,0,-8);
    FTransform Stroke=SwimMeshRest;
    Stroke.SetRotation(Tilt*SwimMeshRest.GetRotation());
    Stroke.SetLocation(Pivot+Tilt.RotateVector(SwimMeshRest.GetLocation()-Pivot));
    P->GetMesh()->SetRelativeTransform(Stroke);
    P->GetMesh()->SetPlayRate(.46f + .7f*FMath::Clamp(M->Velocity.Size()/230.f,0.f,1.f));
    BubbleClock-=Dt;
    RippleClock-=Dt;
    if (SurfaceWeight>.5f && RippleClock<=0 && M->Velocity.Size2D()>15.f){
        Foot = Foot == 1 ? 0 : 1;
        EmitRipple(P->GetMesh()->GetSocketLocation(Foot ? TEXT("hand_l") : TEXT("hand_r")),55.f);
        RippleClock=.35f;
    }
    if (BubbleClock<=0 && SurfaceWeight<.5f){
        const FVector Mouth=P->GetMesh()->GetSocketLocation(TEXT("head"))+P->GetActorForwardVector()*10;
        EmitBubble(Mouth); BubbleClock=FMath::Lerp(.65,.18,FMath::Clamp(M->Velocity.Size()/230.,0.,1.));
    }
}

void AChibiPool::UpdateCamera(float Dt)
{
    auto* Arm=CameraArm.Get();
    auto* PC=GetWorld()->GetFirstPlayerController();
    if (!Arm || !PC || !PC->PlayerCameraManager) return;
    float Target=0;
    if (bSwimming){
        const double Surface=GetActorTransform().TransformPosition(FVector(0,0,WaterZ)).Z;
        const double CameraZ=PC->PlayerCameraManager->GetCameraLocation().Z;
        Target=(1.f-SurfaceWeight)*FMath::Clamp(CameraOffset + Surface - 16. - CameraZ,-160.,0.);
    }
    const float Next=FMath::FInterpTo(CameraOffset,Target,Dt,5.f);
    Arm->TargetOffset.Z+=Next-CameraOffset;
    CameraOffset=Next;
}

void AChibiPool::EmitRipple(FVector Pos,float Diameter)
{
    Pos=GetActorTransform().InverseTransformPosition(Pos);Pos.Z=WaterZ+1.;
    if(Pos.X<0 || Pos.X>PoolLength || FMath::Abs(Pos.Y)>PoolWidth*.5) return;
    Ripples.Add({Pos,Diameter,0,1.f});
}

void AChibiPool::EmitBubble(FVector Pos)
{
    Pos=GetActorTransform().InverseTransformPosition(Pos);
    Pos+=FVector(FMath::FRandRange(-3.f,3.f),FMath::FRandRange(-5.f,5.f),2);
    if (Pos.Z<WaterZ-2) Air.Add({Pos,FMath::FRandRange(1.7f,3.2f),0,FMath::Min(3.f,float(WaterZ-Pos.Z)/34.f)});
}

void AChibiPool::AnimateEffects(float Dt)
{
    auto Animate=[&](TArray<FEffect>& Items,UInstancedStaticMeshComponent* Mesh,bool bRing){
        for(auto& E:Items) E.Age+=Dt;
        Items.RemoveAll([](const FEffect& E){return E.Age>=E.Life;});
        while(Mesh->GetInstanceCount()>Items.Num()) Mesh->RemoveInstance(Mesh->GetInstanceCount()-1);
        for(int i=0;i<Items.Num();++i){
            const auto& E=Items[i]; const float T=E.Age/E.Life;
            FVector Pos=E.Position;
            const float Size=bRing ? E.Size*(.18f+.82f*T) : E.Size*(1.f+.25f*T);
            if(!bRing){Pos.Z+=34*E.Age; Pos.Y+=2*FMath::Sin(E.Age*5);}
            FTransform Transform(FQuat::Identity,Pos,FVector(Size/100.f));
            if(i>=Mesh->GetInstanceCount()) Mesh->AddInstance(Transform);
            else Mesh->UpdateInstanceTransform(i,Transform,false,false,true);
            if(bRing) Mesh->SetCustomDataValue(i,0,1.f-T,false);
        }
        if (Items.Num()) Mesh->MarkRenderStateDirty();
    };
    Animate(Ripples,Rings,true); Animate(Air,Bubbles,false);
}

void AChibiPool::Tick(float Dt)
{
    Super::Tick(Dt);
    auto* PC=GetWorld()->GetFirstPlayerController();
    auto* P=PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
    FVector L=P ? GetActorTransform().InverseTransformPosition(P->GetActorLocation()) : FVector::ZeroVector;
    const float SurfaceDepth=FloorDepth(L.X);
    const float FeetZ=P ? L.Z-P->GetCapsuleComponent()->GetScaledCapsuleHalfHeight() : 0;
    const bool Inside=P && L.X>0 && L.X<PoolLength && FMath::Abs(L.Y)<PoolWidth*.5 && FeetZ<WaterZ && L.Z>WaterZ-PoolDepth-5;
    if(Occupant.Get()!=P || !Inside){if(Occupant.IsValid() || bSwimming) LeaveWater();}
    if(Inside){
        if(Occupant.Get()!=P) EnterWater(*P);
        auto* M=P->GetCharacterMovement();
        const float Wet=WaterZ-FeetZ;
        if(!bSwimming && SurfaceDepth>=100 && Wet>=92) BeginSwimming();
        if(bSwimming && SurfaceDepth<81) EndSwimming();
        if(bSwimming) Swim(Dt,L.Z);
        else {
            const float Wading=FMath::SmoothStep(12.f,80.f,Wet);
            M->MaxWalkSpeed=FMath::Lerp(OldWalkSpeed,FMath::Min(OldWalkSpeed,170.f),Wading);
            const float Speed=M->Velocity.Size2D();
            RippleClock-=Dt;
            if(Speed>15 && M->IsMovingOnGround() && RippleClock<=0){
                const FVector Left=P->GetMesh()->GetSocketLocation(TEXT("foot_l"));
                const FVector Right=P->GetMesh()->GetSocketLocation(TEXT("foot_r"));
                const int LowFoot=Right.Z < Left.Z ? 1 : 0;
                const FVector Boot=LowFoot ? Right : Left;
                const bool Shallow=Wet<18.f;
                if (!Shallow || (LowFoot!=Foot && GetActorTransform().InverseTransformPosition(Boot).Z-8. < WaterZ+2.)){
                    EmitRipple(Boot,FMath::Lerp(26.f,49.f,Wading));
                    Foot=LowFoot;
                }
                if(Wet>28) EmitRipple(P->GetActorLocation(),FMath::Lerp(45.f,96.f,Wading));
                if(Wet>52) EmitRipple(P->GetMesh()->GetSocketLocation(Foot ? TEXT("hand_l") : TEXT("hand_r")),46);
                RippleClock=Shallow ? .025f : FMath::Clamp(65.f/Speed,.15f,.45f);
            }
        }
    }
    UpdateCamera(Dt);
    Underwater->BlendWeight=FMath::FInterpTo(Underwater->BlendWeight,bSwimming ? 1.f-SurfaceWeight : 0.f,Dt,5.f);
    AnimateEffects(Dt);
}
void AChibiPool::EndPlay(const EEndPlayReason::Type Reason)
{
    LeaveWater(); Super::EndPlay(Reason);
}
