#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "ChibiGripTerrainState.h"
#include "ClimbingNet.h"
#include "ClimbingStation.generated.h"

class UBoxComponent;
class UPoseableMeshComponent;

class ACharacter;

UCLASS()
class CHIBICONTACT_API AClimbingStation : public AActor
{
    GENERATED_BODY()
public:
    AClimbingStation();
    virtual void BeginPlay() override;
    UFUNCTION(BlueprintPure, Category="Climbing")
    FVector NetDisplacement(FVector RestPoint) const;
    virtual void Tick(float Delta) override;
    virtual void OnConstruction(const FTransform& Transform) override;
    virtual void EndPlay(const EEndPlayReason::Type Reason) override;
    UPROPERTY(EditAnywhere, Category="Climbing") bool bRopeNet = false;
    UPROPERTY(VisibleAnywhere, Category="Climbing") TObjectPtr<UStaticMeshComponent> Surface;
private:
    UPROPERTY() TObjectPtr<UBoxComponent> Backing;
    UPROPERTY() TObjectPtr<ACharacter> Runner;
    UPROPERTY() TObjectPtr<UPoseableMeshComponent> Pose;
    TUniquePtr<FClimbingNet> Net;
    UPROPERTY() TObjectPtr<UTexture2D> NetOffsets;
    FVector NetContact[4];
    void UpdateNet(float Delta);
    void UploadNet();
    TWeakObjectPtr<APlayerController> MountController;
    double AutoGrabAfter = 0;

    bool WasVisible = true;
    FChibiTerrainHand Contacts[4];
    FIntPoint Cell, Step;
    float Phase = 0;
    int Lead = 0;
    int NextLead = 0;
    TArray<TArray<FVector>> Bands;
    TArray<FVector> FootSupports;
    FVector FootGoal[2], FootFrom[2];
    float FootPhase[2];
    FVector PlaceFoot(int Side, float Delta);
    bool ReadRoute();
    int NearestPair(int Row, float Y) const;
    FVector Anchor(int Limb, FIntPoint Stance) const;
    void Mount(ACharacter* Character, const FVector& LocalPosition);
    void Release();
    void ApplyPose(float Delta);
    void Solve(int Limb, const FVector& Target);
};


