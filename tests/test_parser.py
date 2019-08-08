import pytest

from kfailb import content_parser
import csv

from kfailb import IncidentParser


class TestContentParser:
    @staticmethod
    def _read_stations():
        ret = list()
        with open('stations.csv', newline='') as csv_file:
            content = csv.reader(csv_file, delimiter=';', quotechar='|')
            for index, row in enumerate(content):
                if index != 0:
                    lines = int(row[0])
                    text = row[1]
                    ret.append((lines, text, ))
        return ret

    def test_parse_stations(self):
        parser = IncidentParser()
        read = self._read_stations()
        for testcase in read:
            text, stations = parser.parse_data(testcase[1])
            assert len(stations) == testcase[0]
