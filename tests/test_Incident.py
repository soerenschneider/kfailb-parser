import re

from unittest import TestCase
from kfailb import kfailb_data


class TestIncident(TestCase):
    def test__hash_length(self):
        line = 1
        what = 'Accurate description of the problem'
        stations = []

        incident = kfailb_data.Incident(line, what, stations)

        assert len(incident.hash) == 15

    def test_hash_format(self):
        line = 1
        what = 'Accurate description of the problem'
        stations = []

        incident = kfailb_data.Incident(line, what, stations)

        assert re.match(r'\w{15}', incident.hash)

    def test_hash_equality(self):
        line = 1
        what = 'Accurate description of the problem'
        stations = []

        incident_1 = kfailb_data.Incident(line, what, stations)
        incident_2 = kfailb_data.Incident(line, what, stations)

        assert incident_1.hash == incident_2.hash

    def test_hash_inequality(self):
        line = 1
        what = 'Accurate description of the problem'
        stations = []

        incident_1 = kfailb_data.Incident(line, what, stations)
        incident_2 = kfailb_data.Incident(line + 1, what, stations)

        assert incident_1.hash != incident_2.hash