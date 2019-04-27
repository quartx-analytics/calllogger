# Standard library imports
from unittest import mock
import unittest
import os

# Third party imports
import serial

# Package imports
from monitor import calls, callclasses, dbmanager


class TestParser(unittest.TestCase):
    def test_incoming(self):
        line = "09.09.1821:04:01 1 100 0811111111 0 9923"
        record = calls.parse_serial_line(line)

        self.assertIsInstance(record, callclasses.IncomingCall)

        self.assertEqual("incoming", record.type)
        self.assertEqual("2018-09-09", record["date"])
        self.assertEqual("21:04:01", record["time"])
        self.assertEqual("1", record["line"])
        self.assertEqual("100", record["ext"])
        self.assertEqual("0811111111", record["number"])

    def test_end(self):
        line = "09.09.1820:16:50 1 10000:0100:00:060877629926 1 9923"
        record = calls.parse_serial_line(line)

        self.assertIsInstance(record, callclasses.EndCall)

        self.assertEqual("end", record.type)
        self.assertEqual("2018-09-09", record["date"])
        self.assertEqual("20:16:50", record["time"])
        self.assertEqual("1", record["line"])
        self.assertEqual("100", record["ext"])
        self.assertEqual("0877629926", record["number"])
        self.assertEqual("00:01", record["ring"])
        self.assertEqual("00:00:06", record["duration"])
        self.assertEqual(True, record["answered"])

    def test_outgoing(self):
        line = "02.09.1814:07:40 1 10000:0900:00:000877629926 2"
        record = calls.parse_serial_line(line)

        self.assertIsInstance(record, callclasses.OutgoingCall)

        self.assertEqual("outgoing", record.type)
        self.assertEqual("2018-09-02", record["date"])
        self.assertEqual("14:07:40", record["time"])
        self.assertEqual("1", record["line"])
        self.assertEqual("100", record["ext"])
        self.assertEqual("0877629926", record["number"])
        self.assertEqual("00:09", record["ring"])
        self.assertEqual("00:00:00", record["duration"])
        self.assertEqual(False, record["answered"])


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = db = dbmanager.DataBase()
        self.addCleanup(db.close)

    def tearDown(self):
        os.remove(dbmanager.sqldbfile)

    def test_incoming(self):
        line = "09.09.1821:04:01 1 100 0811111111 0 9923"
        record = calls.parse_serial_line(line)
        self.db.add_call(record)

    def test_end(self):
        line = "09.09.1820:16:50 1 10000:0100:00:060877629926 1 9923"
        record = calls.parse_serial_line(line)
        self.db.add_call(record)

    def test_outgoing(self):
        line = "02.09.1814:07:40 1 10000:0900:00:000877629926 2"
        record = calls.parse_serial_line(line)
        self.db.add_call(record)


class Testmonitor(unittest.TestCase):
    mock_data = ["09.09.1821:04:01 1 100 0811111111 0 9923",
                 "09.09.1820:16:50 1 10000:0100:00:060877629926 1 9923"
                 "02.09.1814:07:40 1 10000:0900:00:000877629926 2",
                 KeyboardInterrupt]

    def test_with_mock(self):
        with mock.patch.object(serial, "Serial", spec=True) as MockClass:
            MockClass.return_value.readline.side_effect = self.mock_data
            calls.monitor()

        os.remove(dbmanager.sqldbfile)
