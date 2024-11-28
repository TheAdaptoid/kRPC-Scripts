from krpc.services.spacecenter import Vessel, SpaceCenter

class Logger:
    def __init__(self, vessel: Vessel, spaceCenter: SpaceCenter) -> None:
        self.vessel: Vessel = vessel
        self.spaceCenter: SpaceCenter = spaceCenter

    def Write_To_Log(self, message: str) -> None:
        print(message)

        with open(f"Flight_Logs/{self.vessel.name}.txt", "a") as file:
            file.write(f"{self.vessel.met} --- {self.vessel.situation.name} --- {message}\n")

    def Clear_Log(self) -> None:
        with open(f"Flight_Logs/{self.vessel.name}.txt", "w") as file:
            file.write("")