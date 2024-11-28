"""
Preliminary Actions
"""
from krpc import connect
from krpc.services.spacecenter import Vessel, Engine, Fairing, Node
from krpc.stream import Stream

from time import sleep
from threading import Thread

CONNECTION = connect(name="Ascent Guidance")
VESSEL: Vessel = CONNECTION.space_center.active_vessel

apoaStream: Stream = CONNECTION.add_stream(getattr, VESSEL.orbit, "apoapsis_altitude")
periStream: Stream = CONNECTION.add_stream(getattr, VESSEL.orbit, "periapsis_altitude")

"""
Functions
"""
