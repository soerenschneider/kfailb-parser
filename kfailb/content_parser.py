import re
import logging

from prometheus_client import Counter
from kfailb.kfailb_data import Incident, Incidents, Station


class IncidentParser:
    _pattern_single_station = re.compile(r"(\D+)\s*(\d+:\d+\s?(\s?h\s?)?)")
    _station_info_pattern = re.compile(r".*\s*\(\s?H\s?\)\s*.*\d{1,2}:\d{1,2}.*")
    _station_info_extract_pattern = re.compile(r"\s*\(\s?H\s?\)\s*")

    _pattern_arbitrary_2 = re.compile(r'\s+\*\s+')
    _pattern_arbitrary_1 = re.compile(r'\s*\*$')

    def __init__(self, metrics_prefix="bla"):
        self._prom_parsing_errors = Counter(f'{metrics_prefix}_parsing_errors_total', 'Description of counter')

    def _contains_station_information(self, text):
        """
        Returns whether the text contains information about stations.
        :param text: the text to check
        :return: True, whether there is station information in the text, otherwise
        False.
        """
        return self._station_info_pattern.match(text) is not None

    def _split_stations(self, stations):
        return re.split(self._station_info_extract_pattern, stations)

    def _parse_station_information(self, text):
        split = text.split('*')
        what = split[0].strip()
        stations = split[1].strip()
        continuum = list()

        for station in self._split_stations(stations):
            if not station:
                continue

            station = station.strip()
            try:
                match = re.search(self._pattern_single_station, station)
                station = match.group(1).strip()
                timestamp = match.group(2).strip()
                continuum.append(Station(station, timestamp))
            except AttributeError as error:
                logging.warning("Can't parse [%s] %s", text, str(error))
                self._prom_parsing_errors.inc()
                return text.strip(), list()

        return what, continuum

    def _parse_problem(self, text):
        if self._contains_station_information(text):
            return self._parse_station_information(text)

        return self._parse_arbitrary(text.strip()), []

    def _parse_arbitrary(self, text):
        text = re.sub(self._pattern_arbitrary_1, '. ', text)
        text = re.sub(self._pattern_arbitrary_2, '. ', text)
        return text

    def parse_data(self, text):
        """
        Entry point for scraping the info page.
        :return: Incidents object containing all the parsed incidents.
        """
        return self._parse_problem(text)
