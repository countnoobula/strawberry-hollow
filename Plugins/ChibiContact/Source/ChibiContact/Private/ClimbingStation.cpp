#include "ClimbingStation.h"
#include "Algo/MinElement.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "RHIResources.h"

#include "Components/BoxComponent.h"
#include "Components/PoseableMeshComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Components/CapsuleComponent.h"
#include "InputCoreTypes.h"

AClimbingStation::AClimbingStation()
{
    PrimaryActorTick.bCanEverTick = true;
    PrimaryActorTick.TickGroup = TG_PostPhysics;
    Surface = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("ClimbingSurface"));
    SetRootComponent(Surface);
    Surface->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Backing = CreateDefaultSubobject<UBoxComponent>(TEXT("PanelCollision"));
    Backing->SetupAttachment(Surface);
    Backing->SetCollisionProfileName(TEXT("BlockAll"));
}
void AClimbingStation::BeginPlay()
{
    Super::BeginPlay();
    if(!bRopeNet) return;
    Net=MakeUnique<FClimbingNet>();
    Net->Initialize();
    NetOffsets=UTexture2D::CreateTransient(Net->Cols,Net->Rows,PF_A32B32G32R32F);
    NetOffsets->SRGB=false; NetOffsets->Filter=TF_Bilinear;
    NetOffsets->AddressX=TA_Clamp; NetOffsets->AddressY=TA_Clamp;
    NetOffsets->UpdateResource();
    for(FName Slot:{FName(TEXT("Flax")),FName(TEXT("Ochre")),FName(TEXT("Binding"))}){
        int Index=Surface->GetMaterialIndex(Slot);
        if(Index!=INDEX_NONE){
            if(auto* MID=Surface->CreateDynamicMaterialInstance(Index)){
                MID->SetTextureParameterValue(TEXT("NetOffsets"),NetOffsets);
                MID->SetScalarParameterValue(TEXT("LiveNet"),1);
            }
        }
    }
    Surface->SetBoundsScale(1.4f);
    UploadNet();
}
FVector AClimbingStation::NetDisplacement(FVector RestPoint) const
{
    return Net ? Net->Offset(RestPoint) : FVector::ZeroVector;
}
void AClimbingStation::UploadNet()
{
    static const FUpdateTextureRegion2D Region(0,0,0,0,FClimbingNet::Cols,FClimbingNet::Rows);
    auto* Pixels=new FLinearColor[FClimbingNet::Count];
    for(int I=0;I<Net->Count;++I){
        FVector D=Net->Position[I]-Net->Rest[I];
        Pixels[I]=FLinearColor(D.X,D.Y,D.Z,1);
    }
    NetOffsets->UpdateTextureRegions(0,1,&Region,Net->Cols*sizeof(FLinearColor),sizeof(FLinearColor),
        reinterpret_cast<uint8*>(Pixels),[](uint8* Data,const FUpdateTextureRegion2D*){delete[] reinterpret_cast<FLinearColor*>(Data);});
}
void AClimbingStation::UpdateNet(float Delta)
{
    if(!Net) return;
    if(Runner){
        double Weight=0;
        for(int I=0;I<4;++I) if(Contacts[I].bLocked) Weight+=I<2?.32:.18;
        for(int I=0;I<4;++I) if(Contacts[I].bLocked && Weight>0){
            const double Share=(I<2?.32:.18)/Weight;
            Net->Load(NetContact[I],Share*FVector(-4300,0,-4800));
        }
    }
    if(Net->Advance(Delta)) UploadNet();
}
void AClimbingStation::OnConstruction(const FTransform& Transform)
{
    Super::OnConstruction(Transform);
    Backing->SetRelativeLocation(FVector(7,0,138));
    Backing->SetBoxExtent(FVector(6,bRopeNet ? 70 : 150,138));
}
bool AClimbingStation::ReadRoute()
{
    Bands.Reset(); FootSupports.Reset();
    for (int Row=0; ; ++Row){
        TArray<FVector> Band;
        for (int Col=0; ; ++Col){
            FName Name(*FString::Printf(TEXT("Grip_%d_%d"),Row,Col));
            if (!Surface->DoesSocketExist(Name)) break;
            Band.Add(Surface->GetSocketTransform(Name,RTS_Component).GetLocation());
        }
        if (Band.Num()<2) break;
        FootSupports.Append(Band); Bands.Add(MoveTemp(Band));
    }
    for(int I=0;;++I){
        FName Name(*FString::Printf(TEXT("Toe_%d"),I));
        if (!Surface->DoesSocketExist(Name)) break;
        FootSupports.Add(Surface->GetSocketTransform(Name,RTS_Component).GetLocation());
    }
    return Bands.Num()>=2;
}
int AClimbingStation::NearestPair(int Row,float Y) const
{
    int Best=INDEX_NONE; double Distance=BIG_NUMBER;
    const auto& Band=Bands[Row];
    for(int I=0;I+1<Band.Num();++I){
        if ((Band[I+1]-Band[I]).Size()>46) continue;
        double D=FMath::Abs(.5*(Band[I].Y+Band[I+1].Y)-Y);
        if (D<Distance){Best=I;Distance=D;}
    }
    return Best;
}
FVector AClimbingStation::Anchor(int Limb, FIntPoint Stance) const
{
    if (!bRopeNet){
        FVector Grip=Bands[Stance.Y+1][Stance.X+Limb%2];
        if (Limb>=2){
            const FVector Ideal=Grip-FVector(0,0,35);
            const auto& Lower=Bands[Stance.Y];
            Grip=*Algo::MinElementBy(Lower,[&](const FVector& P){return (P-Ideal).SizeSquared();});
        }
        return Grip+FVector(Limb<2?-3:-5,Limb<2?(Limb==0?-2.2f:2.2f):0,Limb<2?1:5);
    }
    int Column = Stance.X + ((Limb % 2) ? 0 : -1);
    int Row = Stance.Y + (Limb < 2 ? 2 : 0);
    float Y = 20*Column + 10;

    // Wrist sits behind the palm. Ankle sits behind and above the toe.
    return FVector((bRopeNet ? -19.f : -4.f) - (Limb<2 ? 2.8f : 5.f),Y,16+16*Row+(Limb<2 ? 1.f : 6.f));
}
void AClimbingStation::Mount(ACharacter* Character, const FVector& LocalPosition)
{
    if (!bRopeNet && !ReadRoute()) return;
    if (bRopeNet){
        double Best=BIG_NUMBER;
        for(int Row=0;Row<=13;++Row) for(int Col=-2;Col<=2;++Col){
            FIntPoint Candidate(Col,Row);
            FVector Knot=Anchor(0,Candidate)+FVector(0,10,-1);
            FVector Center=Knot+NetDisplacement(Knot);
            double Distance=FMath::Square(LocalPosition.Y-Center.Y)+FMath::Square(LocalPosition.Z-Center.Z-10);
            if(Distance<Best){Best=Distance; Cell=Candidate;}
        }
    } else {
        double Best=BIG_NUMBER;
        for(int Row=1;Row<Bands.Num();++Row){
            const int Col=NearestPair(Row,LocalPosition.Y);
            if(Col==INDEX_NONE) continue;
            const FVector Mid=(Bands[Row][Col]+Bands[Row][Col+1])*.5;
            const double Distance=FMath::Square(Mid.Y-LocalPosition.Y)
                +FMath::Square(Mid.Z-(LocalPosition.Z-10));
            if(Distance<Best){ Best=Distance; Cell=FIntPoint(Col,Row-1); }
        }
        if(Best==BIG_NUMBER) return;
    }
    Runner=Character;
    MountController=CastChecked<APlayerController>(Runner->GetController());
    Step=FIntPoint::ZeroValue; Phase=0; NextLead=0;
    for(int I=0;I<4;++I){ Contacts[I].Support=Surface; Contacts[I].LocalPoint=Anchor(I,Cell); Contacts[I].bLocked=true; }
    for(int I=0;I<2;++I){FootGoal[I]=Contacts[2+I].LocalPoint;FootFrom[I]=FootGoal[I];FootPhase[I]=1;}
    MountController->SetIgnoreMoveInput(true);
    Runner->GetCharacterMovement()->StopMovementImmediately();
    Runner->GetCharacterMovement()->DisableMovement();
    auto* Mesh=Runner->GetMesh();
    Pose=NewObject<UPoseableMeshComponent>(Runner);
    Pose->SetSkinnedAssetAndUpdate(Mesh->GetSkeletalMeshAsset());
    Pose->SetupAttachment(Mesh); Pose->SetCollisionEnabled(ECollisionEnabled::NoCollision);
    Pose->RegisterComponent();
    for(int I=0;I<Mesh->GetNumMaterials();++I) Pose->SetMaterial(I,Mesh->GetMaterial(I));
    WasVisible=Mesh->IsVisible(); Mesh->SetVisibility(false,false);
    ApplyPose(0);
}
void AClimbingStation::Release()
{
    if (!Runner) return;
    if (Pose) Pose->DestroyComponent();
    Pose=nullptr;
    Runner->GetMesh()->SetVisibility(WasVisible,false);
    AutoGrabAfter=GetWorld()->GetTimeSeconds()+.4;
    Runner->SetActorLocation(Runner->GetActorLocation()-GetActorForwardVector()*42);
    Runner->GetCharacterMovement()->SetMovementMode(MOVE_Falling);
    if(MountController.IsValid()) MountController->SetIgnoreMoveInput(false);
    MountController.Reset();
    Runner=nullptr;
}
void AClimbingStation::EndPlay(const EEndPlayReason::Type Reason)
{
    Release(); Super::EndPlay(Reason);
}
void AClimbingStation::Tick(float Delta)
{
    Super::Tick(Delta);
    UpdateNet(Delta);
    auto* PC=GetWorld()->GetFirstPlayerController();
    if (!PC) return;
    if (!Runner){
        auto* Player=Cast<ACharacter>(PC->GetPawn());
        if (!Player) return;
        const FVector P=GetActorTransform().InverseTransformPosition(Player->GetActorLocation());
        if(P.X>=4 || P.X<=-95 || FMath::Abs(P.Y)>=(bRopeNet?60:140) || P.Z<=0) return;
        const bool Manual=PC->WasInputKeyJustPressed(EKeys::E) && P.Z<110;
        const double GrabDepth=Player->GetCapsuleComponent()->GetScaledCapsuleRadius()+(bRopeNet?23:8);
        const auto* Movement=Player->GetCharacterMovement();
        const FVector Normal=GetActorForwardVector();
        const bool Approaching=FVector::DotProduct(Player->GetVelocity(),Normal)>5
            || FVector::DotProduct(Movement->GetCurrentAcceleration(),Normal)>5;
        const bool AutoGrab=P.X>=-GrabDepth && P.Z<=264
            && GetWorld()->GetTimeSeconds()>=AutoGrabAfter && Approaching;
        if(Manual || AutoGrab) Mount(Player,P);
        return;
    }
    if(PC->GetPawn()!=Runner || PC->WasInputKeyJustPressed(EKeys::E) || PC->WasInputKeyJustPressed(EKeys::SpaceBar)){Release();return;}
    int Vertical=int(PC->IsInputKeyDown(EKeys::W)||PC->IsInputKeyDown(EKeys::Up))-int(PC->IsInputKeyDown(EKeys::S)||PC->IsInputKeyDown(EKeys::Down));
    int Horizontal=int(PC->IsInputKeyDown(EKeys::D)||PC->IsInputKeyDown(EKeys::Right))-int(PC->IsInputKeyDown(EKeys::A)||PC->IsInputKeyDown(EKeys::Left));
    if (Step==FIntPoint::ZeroValue){
        FIntPoint Request(!Vertical && !bRopeNet ? Horizontal : 0,Vertical);
        FIntPoint Dest=Cell+Request;
        bool Valid=false;
        if (bRopeNet) Valid=Vertical && Dest.Y>=0 && Dest.Y<=13;
        else if (Request!=FIntPoint::ZeroValue && Bands.IsValidIndex(Dest.Y+1) && Dest.Y>=0){
            const auto& Band=Bands[Dest.Y+1];
            if(Vertical){
                double Mid=(Anchor(0,Cell).Y+Anchor(1,Cell).Y)*.5;
                Dest.X=NearestPair(Dest.Y+1,Mid);
            }
            Valid=Dest.X>=0 && Band.IsValidIndex(Dest.X+1) && (Band[Dest.X+1]-Band[Dest.X]).Size()<46;
            if (Valid && Vertical){
                // A missing section can require a traverse before the next upward move.
                double Span=FMath::Min((Anchor(0,Dest)-Anchor(1,Cell)).Size(),(Anchor(1,Dest)-Anchor(0,Cell)).Size());
                Valid=Span<55 && (Anchor(0,Dest)-Anchor(0,Cell)).Size()<58 && (Anchor(1,Dest)-Anchor(1,Cell)).Size()<58;
            }
        }
        if(Valid){
            Step=Dest-Cell;
            Lead=Vertical ? NextLead : int(Horizontal<0); // Match on the shared hold before reaching out.
            if (Vertical && !bRopeNet){
                // Start with the crossover that requires less shoulder span.
                float Left=(Anchor(0,Dest)-Anchor(1,Cell)).Size();
                float Right=(Anchor(1,Dest)-Anchor(0,Cell)).Size();
                if(FMath::Abs(Left-Right)>4) Lead=int(Right<Left);
            }
            Phase=0;
        }
    }
    if(Step!=FIntPoint::ZeroValue){
        Phase=FMath::Min(1.f,Phase+Delta/(bRopeNet?.68f:.94f));
        if(Phase>=1){Cell+=Step;Step=FIntPoint::ZeroValue;Phase=0;NextLead=1-Lead;
            for(int I=0;I<4;++I) Contacts[I].LocalPoint=Anchor(I,Cell);}
    }
    ApplyPose(Delta);
}
FVector AClimbingStation::PlaceFoot(int Side,float Delta)
{
    FName Thigh=Side ? TEXT("thigh_r") : TEXT("thigh_l");
    FVector Hip=GetActorTransform().InverseTransformPosition(Pose->GetBoneTransformByName(Thigh,EBoneSpaces::WorldSpace).GetLocation());
    FVector Ideal=Hip+FVector(7,Side?2:-2,-11);
    // Retain a weighted foot until the hip leaves its working range.
    if (FootPhase[Side]>=1 && ((FootGoal[Side]-Hip).Size()>18.7 || FootGoal[Side].X>-6 || (FootGoal[Side]-FootGoal[1-Side]).Size()<10)){
        FVector Best=FVector(-4.5,Ideal.Y,Ideal.Z); // Friction smear between resin supports.
        double Score=BIG_NUMBER;
        for(const FVector& Grip:FootSupports){
            FVector Ankle=Grip+FVector(-5,0,5);
            if ((Ankle-FootGoal[1-Side]).Size()<10 || (Ankle-Hip).Size()>18.5 || Ankle.Z>Hip.Z+8) continue;
            double D=(Ankle-Ideal).SizeSquared();
            if(D<Score){Score=D;Best=Ankle;}
        }
        if((Best-FootGoal[Side]).Size()>2.5){FootFrom[Side]=FootGoal[Side];FootGoal[Side]=Best;FootPhase[Side]=0;}
    }
    FootPhase[Side]=FMath::Min(1.f,FootPhase[Side]+Delta/.18f);
    float T=FMath::SmoothStep(0.f,1.f,FootPhase[Side]);
    return FMath::Lerp(FootFrom[Side],FootGoal[Side],T)-FVector(2*FMath::Sin(PI*T),0,0);
}
void AClimbingStation::ApplyPose(float Delta)
{
    FVector Targets[4];
    for(int I=0;I<4;++I){
        bool First=(I%2==Lead) != (I>=2);
        float Reach=FMath::Clamp(Phase*2-(First?0.f:1.f),0.f,1.f);
        float T=FMath::SmoothStep(.12f,.86f,Reach);
        Targets[I]=FMath::Lerp(Contacts[I].LocalPoint,Anchor(I,Cell+Step),T);
        Targets[I].X-=(bRopeNet?3:5)*FMath::Sin(PI*T);
        Contacts[I].bLocked=T==0.f || T==1.f;
        if(Net){
            NetContact[I]=Targets[I]-FVector(0,0,I<2?1:6);
            Targets[I]+=Net->Offset(NetContact[I]);
        }
    }
    FVector Mid=(Targets[0]+Targets[1])*.5;
    float Pulse=FMath::Sin(Phase*2*PI);
    float Lean=bRopeNet ? 0 : FMath::Clamp(FMath::RadiansToDegrees(FMath::Atan2(Targets[1].Z-Targets[0].Z,FMath::Max(17.,Targets[1].Y-Targets[0].Y))),-42.,42.);
    // Roll the shoulder line towards the higher grip; the hips counterbalance beneath it.
    const FQuat Tilt(FVector::ForwardVector,FMath::DegreesToRadians(Lean));
    FVector ShoulderOffset=Tilt.RotateVector(FVector(0,0,22));
    FVector Base=Mid-FVector(bRopeNet?13:12,ShoulderOffset.Y,ShoulderOffset.Z+26+7-60);
    Base.Y+=(Lead?-1:1)*Pulse*(bRopeNet?1.7:3.6);
    Base.Z-=2.8*FMath::Square(FMath::Sin(Phase*2*PI));
    Runner->SetActorLocationAndRotation(GetActorTransform().TransformPosition(Base),GetActorRotation(),false,nullptr,ETeleportType::TeleportPhysics);
    Pose->ResetBoneTransformByName(TEXT("spine_01"));
    auto Spine=Pose->GetBoneTransformByName(TEXT("spine_01"),EBoneSpaces::WorldSpace);
    Spine.SetRotation(FQuat(GetActorForwardVector(),FMath::DegreesToRadians(Lean))*Spine.GetRotation());
    Pose->SetBoneTransformByName(TEXT("spine_01"),Spine,EBoneSpaces::WorldSpace);
    // Keep her gaze up the route while the ribcage rolls underneath the head.
    Pose->ResetBoneTransformByName(TEXT("neck_01"));
    FTransform Neck=Pose->GetBoneTransformByName(TEXT("neck_01"),EBoneSpaces::WorldSpace);
    Neck.AddToTranslation(-GetActorForwardVector()*2.5);
    Neck.SetRotation(FQuat(GetActorRightVector(),FMath::DegreesToRadians(-22.))*FQuat(GetActorForwardVector(),FMath::DegreesToRadians(-Lean*.75))*Neck.GetRotation());
    Pose->SetBoneTransformByName(TEXT("neck_01"),Neck,EBoneSpaces::WorldSpace);
    for(int I=0;I<4;++I){
        if (!bRopeNet && I>=2) Targets[I]=PlaceFoot(I-2,Delta);
        Contacts[I].Point=Surface->GetComponentTransform().TransformPosition(Targets[I]);
        Solve(I,Contacts[I].Point);
    }
    Pose->RefreshBoneTransforms();
}
void AClimbingStation::Solve(int Limb,const FVector& Target)
{
    static const FName Chains[4][3]={{TEXT("upperarm_l"),TEXT("lowerarm_l"),TEXT("hand_l")},{TEXT("upperarm_r"),TEXT("lowerarm_r"),TEXT("hand_r")},{TEXT("thigh_l"),TEXT("calf_l"),TEXT("foot_l")},{TEXT("thigh_r"),TEXT("calf_r"),TEXT("foot_r")}};
    auto Read=[&](int Index){return Pose->GetBoneTransformByName(Chains[Limb][Index],EBoneSpaces::WorldSpace);};
    auto Write=[&](int Index,const FTransform& T){Pose->SetBoneTransformByName(Chains[Limb][Index],T,EBoneSpaces::WorldSpace);};
    // Start from the rig's local rotations each frame to avoid accumulating twist.
    for(int I=0;I<3;++I) Pose->ResetBoneTransformByName(Chains[Limb][I]);
    FTransform Upper=Read(0),Lower=Read(1),Tip=Read(2);
    FVector A=Upper.GetLocation(),B=Lower.GetLocation(),C=Tip.GetLocation();
    double L1=(B-A).Length(),L2=(C-B).Length();
    FVector Dir=(Target-A).GetSafeNormal();
    if(Limb<2 || !bRopeNet){
        // Shoulder protraction supplies the last few centimetres at full extension.
        double Reach=FMath::Max(0.,(Target-A).Size()-L1-L2+.02);
        if(Limb>=2) Reach=FMath::Min(Reach,2.0);
        if(Reach>0){
            FVector Offset=Dir*Reach;
            Upper.AddToTranslation(Offset); Write(0,Upper);
            A+=Offset;B+=Offset;C+=Offset;
        }
    }
    double D=FMath::Clamp((Target-A).Length(),FMath::Abs(L1-L2)+.001,L1+L2-.001);
    double Along=(D*D+L1*L1-L2*L2)/(2*D);
    FVector Pole=GetActorTransform().TransformVectorNoScale(FVector(Limb<2?-.6:.8,(Limb%2?1:-1)*(Limb<2?1.:.65),Limb<2?-1.:.15));
    FVector Joint=A+Dir*Along+FVector::VectorPlaneProject(Pole,Dir).GetSafeNormal()*FMath::Sqrt(FMath::Max(0.,L1*L1-Along*Along));
    Upper.SetRotation(FQuat::FindBetweenNormals((B-A).GetSafeNormal(),(Joint-A).GetSafeNormal())*Upper.GetRotation()); Write(0,Upper);
    Lower=Read(1);FVector End=Read(2).GetLocation();
    Lower.SetRotation(FQuat::FindBetweenNormals((End-Lower.GetLocation()).GetSafeNormal(),(Target-Lower.GetLocation()).GetSafeNormal())*Lower.GetRotation());Write(1,Lower);
    FTransform Final=Read(2);Final.SetRotation(Tip.GetRotation());Write(2,Final);
}







