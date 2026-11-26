#include "ChibiRopeSwing.h"

void UChibiRopeSwing::AdvanceRopeSwing(double DeltaSeconds, double Angle, double AngularVelocity,
    double RopeLength, double Input, double PumpAccel, double MaxAngle, double& NextAngle, double& NextVelocity)
{
    const double Gravity = 980. / FMath::Max(1., RopeLength);
    const double Arc = FMath::Clamp(MaxAngle + FMath::DegreesToRadians(20.), .1, FMath::DegreesToRadians(85.));
    const double ArcEnergy = Gravity * (1. - FMath::Cos(Arc));
    const double Drive = FMath::Clamp(Input, -1., 1.) * FMath::Clamp(PumpAccel, 0., .24 * Gravity);

    // A held lean shifts the balance point. Reversing it with the travel
    // direction does positive work on both halves of the swing.
    const double Time = FMath::Clamp(DeltaSeconds, 0., .25);
    const int Steps = FMath::Max(1, FMath::CeilToInt(Time * 120.));
    const double Dt = Time / Steps;
    for (int Index = 0; Index < Steps; ++Index)
    {
        const double Energy = .5 * AngularVelocity * AngularVelocity + Gravity * (1. - FMath::Cos(Angle));
        const double Ratio = Energy / ArcEnergy;
        const double Assist = 1. - FMath::SmoothStep(.72, 1., Ratio);
        const double Drag = .12 + 3. * FMath::Max(0., Ratio - 1.);
        AngularVelocity += Dt * (Drive * Assist * FMath::Cos(Angle) - Gravity * FMath::Sin(Angle) - Drag * AngularVelocity);
        Angle += Dt * AngularVelocity;
    }
    NextAngle = Angle;
    NextVelocity = AngularVelocity;
}
