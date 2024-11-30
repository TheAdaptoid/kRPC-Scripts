from krpc.services.spacecenter import Part, Vessel, SpaceCenter, SASMode
from time import sleep
from Flight_Logger import Logger
from math import sqrt

class Rocket_Guidance:
    def __init__(self, vessel: Vessel, logger: Logger, spaceCenter: SpaceCenter, targApo: int = 80000) -> None:
        self.vessel: Vessel = vessel
        self.logger: Logger = logger
        self.spaceCenter: SpaceCenter = spaceCenter
        self.targApo: int = targApo

    def _Calc_Orbital_Speed(self) -> float:
        bodyMass: float = self.vessel.orbit.body.mass
        numerator: float = self.spaceCenter.g * bodyMass
        demoninator: float = self.targApo + self.vessel.orbit.body.equatorial_radius
        return round(
            number=sqrt(numerator / demoninator),
            ndigits=4
        )
    
    def _Get_Speed_At_Apo(self) -> float:
        return self.vessel.orbit.orbital_speed_at(
            time=self.vessel.orbit.time_to_apoapsis + self.spaceCenter.ut
        )
    
    def _Time_Til_Acceleration(self) -> float:
        idealSpeed: float = self._Calc_Orbital_Speed()
        currentSpeed: float = self._Get_Speed_At_Apo()

        numerator: float = idealSpeed - currentSpeed
        demoninator: float = self.vessel.available_thrust / self.vessel.mass

        return round(
            number=numerator / demoninator,
            ndigits=4
        )
    
    def _UT_Burn_Start(self) -> float:
        return self.vessel.orbit.time_to_apoapsis + self.spaceCenter.ut - (self._Time_Til_Acceleration() / 2)

    def Run(self) -> None:
        self.Countdown(5)
        self.Launch()

        # Lock Control
        self.vessel.auto_pilot.engage()
        self.vessel.auto_pilot.sas = True
        self.vessel.control.rcs = True

        # Ascent and Gravity Turn
        self.vessel.control.throttle = 1
        while self.vessel.orbit.apoapsis_altitude < self.targApo:
            # Check staging
            self.Fire_Stage()

            # Gravity turn control
            targetPitch: float = 90 - abs(self.vessel.orbit.apoapsis_altitude / self.targApo) * 90
            self.vessel.auto_pilot.target_pitch = targetPitch
        self.vessel.control.throttle = 0
        self.logger.Write_To_Log("Ascent Complete!")

        # Coast
        utBurnStart: float = self._UT_Burn_Start()
        while self.spaceCenter.ut < utBurnStart:
            self.vessel.auto_pilot.target_pitch = 0

        # Orbital Insertion
        self.vessel.control.throttle = 1
        while self.vessel.orbit.speed <= self._Calc_Orbital_Speed() or self.vessel.control.current_stage == 0:
            # Check staging
            self.Fire_Stage()
        self.vessel.control.throttle = 0
        self.logger.Write_To_Log("Orbital Insertion Complete!")

        # Coast
        sleep(5)

        # Descent
        self.vessel.auto_pilot.sas = True
        while self.vessel.orbit.periapsis_altitude > self.vessel.orbit.body.equatorial_radius or self.vessel.control.current_stage == 0:
            # Check staging
            self.Fire_Stage()

            self.vessel.auto_pilot.sas_mode = SASMode.retrograde
            self.vessel.control.throttle = 1
        self.vessel.control.throttle = 0
        self.logger.Write_To_Log("Descent Complete!")

        # Unlock Control
        self.vessel.auto_pilot.disengage()
        self.vessel.auto_pilot.sas = False
        self.vessel.control.rcs = False

    def Fire_Stage(self) -> None:
        if self.vessel.available_thrust <= 0 and self.vessel.control.current_stage != 0:
            self.logger.Write_To_Log(f"Fired Stage {self.vessel.control.current_stage}")
            self.vessel.control.activate_next_stage()
    
    def Launch(self) -> None:
        padStage: int = self.vessel.control.current_stage - 1 # Bottom stage + 1
        firstStageParts: list[Part] = self.vessel.parts.in_stage(stage=padStage)

        for part in firstStageParts:
            if part.engine is not None:
                part.engine.active = True

            if part.launch_clamp is not None:
                part.launch_clamp.release()
    
    def Countdown(self, seconds: int = 10) -> None:
        for i in range(seconds, 0, -1):
            print(f"T - {i}")
            sleep(1)
        self.logger.Write_To_Log("Lift Off!")