from krpc.services.spacecenter import Part, Vessel
from time import sleep
from Flight_Logger import Logger

class Ascent_Guidance:
    def __init__(self, vessel: Vessel, logger: Logger, targAlt: int = 80000) -> None:
        self.vessel: Vessel = vessel
        self.logger: Logger = logger
        self.targAlt: int = targAlt
        pass

    def Run(self) -> None:
        self.Countdown(5)
        self.Launch()

        while self.vessel.orbit.apoapsis_altitude < self.targAlt:
            self.vessel.control.throttle = 1
            self.Fire_Stage()

            # Gravity turn control
            targetPitch: float = 90 - abs(self.vessel.orbit.apoapsis_altitude / self.targAlt) * 90
            self.vessel.auto_pilot.target_pitch = targetPitch
        self.vessel.control.throttle = 0
        self.logger.Write_To_Log("Ascent Complete!")

        # Coast
        while self.vessel.flight().mean_altitude < 71000:
            sleep(0.1)

        while self.vessel.flight().mean_altitude >= 70000 and self.vessel.orbit.periapsis_altitude <= self.targAlt:
            self.vessel.control.throttle = 1
            self.Fire_Stage()

            # Orbital Insertion
            self.vessel.auto_pilot.target_pitch = 0
        self.vessel.control.throttle = 0
        self.logger.Write_To_Log("Orbital Insertion Complete!")


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