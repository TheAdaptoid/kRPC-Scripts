import krpc

from os import system
from time import sleep
from threading import Thread
from krpc.services.spacecenter import Vessel
from Science_Core import Science_Core
from Rocket_Guidance_2 import Rocket_Guidance
from Flight_Logger import Logger

CONNECTION = krpc.connect(name="Series A - Guidance Computer")
vessel: Vessel = CONNECTION.space_center.active_vessel

logger: Logger = Logger(vessel, CONNECTION.space_center)
scienceCore: Science_Core = Science_Core(vessel, logger)
ascentCore: Rocket_Guidance = Rocket_Guidance(vessel, logger, CONNECTION.space_center)

system("cls")

def Science_Core_Thread():
    scienceCore.Run()

def Ascent_Core_Thread():
    ascentCore.Run()

def Main():
    logger.Clear_Log()

    ascentCoreThread = Thread(target=Ascent_Core_Thread)
    ascentCoreThread.start()

    scienceCoreThread = Thread(target=Science_Core_Thread)
    scienceCoreThread.start()

Main()