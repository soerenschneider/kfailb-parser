"""
Definition of dataclasses used by kfailb.
"""

from dataclasses import dataclass, field
from typing import List
import datetime
import hashlib


@dataclass
class Station:
    """
    Tuple of a station and a given time.
    """
    station: str
    time: str

    def __repr__(self):
        return f'{self.station} ({self.time})'


@dataclass
class Incident:
    """
    Holds information about a single incident.
    """
    # what line is affected by the incident.
    line: int

    # information about the incident.
    what: str

    # list of stations that are affected. may be empty.
    stations: List[Station]

    # the same line goes in two directions, from a -> z and from z -> a. if there is information about affected
    # stations, a string is being built that indicates the direction of an incident. is empty if no stations
    # information is available.
    direction: str = field(init=False)

    # the hash is used by consuming clients to easily determine whether a message has been processed already.
    # it consists of a unix timestamp and a truncated sha256 hex-digested hash, in the format '<timestamp>-<hash>'.
    hash: str = ""

    def __post_init__(self):
        self.direction = self.__gen_direction()

        self.hash = self.__gen_hash()

    def __gen_direction(self):
        """
        Generates the directions string.
        :return: None if there are no stations, otherwise a string that denotes the direction.
        """
        if self.stations:
            return "{} -> {}".format(self.stations[0].station,
                                     self.stations[len(self.stations)-1].station)

        return None

    def __gen_hash(self):
        """
        Generates the hash for this object.
        :return: the hash
        """
        representation = str(self)
        sha256 = hashlib.sha256(representation.encode('utf-8')).hexdigest()[:15]

        return sha256

    def __repr__(self):
        return f'{self.line}: {self.direction}: {self.what}\n{self.stations}\n'


@dataclass
class Incidents:
    """
    List of incidents in combination with a timestamp.
    """
    incidents: List = field(default_factory=lambda: [])
    time_stamp: str = field(init=False)

    def __post_init__(self):
        self.time_stamp = datetime.datetime.now().isoformat()

    def __repr__(self):
        return f'{self.incidents}\n'

    def __str__(self):
        return f'{self.incidents}\n'
