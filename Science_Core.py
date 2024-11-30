from krpc.services.spacecenter import Part, Experiment, Vessel
from Flight_Logger import Logger

class Experiment_Queue:
    def __init__(self):
        self.queue: list[Experiment] = []

    def isEmpty(self) -> bool:
        return len(self.queue) == 0

    def Enqueue(self, experiment: Experiment) -> None:
        if type(experiment) is not Experiment:
            raise TypeError
        
        self.queue.append(experiment)

    def Dequeue(self) -> Experiment:
        item: Experiment = self.queue[0]
        self.queue = self.queue[1:] # Shift queue
        return item

class Science_Core:
    def __init__(self, vessel: Vessel, logger: Logger, minSciThreshold: float = 0.8):
        self.vessel: Vessel = vessel
        self.experimentQueue: Experiment_Queue = Experiment_Queue()
        self.transmissionQueue: Experiment_Queue = Experiment_Queue()
        self.experimentLog: list[str] = []
        self.logger: Logger = logger
        self.minSciThreshold: float = minSciThreshold

    def Store_Science(self) -> None:
        raise NotImplementedError
    
    def _Calc_Transmission_Cost(self, experiment: Experiment, antenna: Part) -> float:
        packets: int = experiment.data[-1].data_amount / antenna.antenna.packet_size
        return packets * antenna.antenna.packet_resource_cost
    
    def _Get_Best_Antenna(self) -> Part:
        antennas: list[Part] = [part for part in self.vessel.parts.all if part.antenna is not None]
        antennas.sort(key=lambda antenna: antenna.antenna.power)
        return antennas[0]
    
    def Transmit_Science(self) -> None:
        # Get best antenna
        bestAntenna: Part = self._Get_Best_Antenna()

        while not self.transmissionQueue.isEmpty():
            experiment: Experiment = self.transmissionQueue.Dequeue()

            for scienceData in experiment.data:
                if scienceData.transmit_value > 0 and bestAntenna.antenna.can_transmit:
                    transmitCost: float = self._Calc_Transmission_Cost(experiment, bestAntenna)
                    if self.vessel.resources.amount("Electric Charge") > transmitCost:
                        experiment.transmit()

                        self.logger.Write_To_Log(f"Transmitting experiment: {experiment.science_subject.title} @ {transmitCost} EC")

                else:
                    pass # Push to storage

    def Conduct_Science(self) -> None:
        while not self.experimentQueue.isEmpty():
            experiment: Experiment = self.experimentQueue.Dequeue()

            # Check if experiment has already been conducted
            if experiment.science_subject.title not in self.experimentLog:

                # Run experiment and add to log
                experiment.run()
                self.experimentLog.append(experiment.science_subject.title)
                self.logger.Write_To_Log(f"Conducting experiment: {experiment.science_subject.title}")

                # Add experiment to transmission queue
                self.transmissionQueue.Enqueue(experiment)

    def Detect_Science(self) -> None:

        # Get parts with science modules
        scienceParts: list[Part] = [part for part in self.vessel.parts.all if part.experiment is not None]
        experiments: list[Experiment] = [experiment for part in scienceParts for experiment in part.experiments]

        # Iterate through experiments
        for experiment in experiments:
            # Check if the experiment can be conducted
            if (
                # Must not have data
                not experiment.has_data
            ) and (
                # Can be deployed in the current situation
                experiment.available and not experiment.inoperable
            ) and (
                # Must have available science to collect
                (experiment.science_subject.science / experiment.science_subject.science_cap) < self.minSciThreshold
            ):
                # Add to queue
                self.experimentQueue.Enqueue(experiment)

            # Check if the experiment can be transmitted
            for data in experiment.data:
                if data.transmit_value > 0:
                    self.transmissionQueue.Enqueue(experiment)

        # Conduct queued experiments
        self.Conduct_Science()
        self.Transmit_Science()

    def Run(self) -> None:
        while True:
            if self.vessel.met > 10: self.Detect_Science()