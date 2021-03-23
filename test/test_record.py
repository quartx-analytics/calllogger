# Standard Lib
from datetime import datetime, timezone

# Third Party
import pytest

# Local
from calllogger.record import CallDataRecord


@pytest.fixture
def record():
    return CallDataRecord(call_type=2)


@pytest.mark.parametrize("call_type", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 35, 36, 37, 38])
def test_call_types(call_type):
    record = CallDataRecord(call_type)
    assert record.call_type == call_type


def test_date(record):
    fmt = "%d.%m.%y%X"
    tz = timezone.utc
    date = datetime.now().replace(microsecond=0, tzinfo=tz)
    record.date(date.strftime(fmt), fmt=fmt, tz=tz)
    assert "date" in record.data
    assert record.data["date"] == date.isoformat()


@pytest.mark.parametrize("date", ["", " "])
def test_invalid_date(record, date):
    before = record.data["date"]
    record.date(date)
    assert "date" in record.data
    assert record.data["date"] == before


@pytest.mark.parametrize("number", ["0876159281", "066715325"])
def test_number(record, number):
    record.number = number
    assert "number" in record.data
    assert record.number == number


@pytest.mark.parametrize("number", ["", " "])
def test_invalid_number(record, number):
    record.number = number
    assert "number" not in record.data


@pytest.mark.parametrize("line", ["1", 2])
def test_line(record, line):
    record.line = line
    assert "line" in record.data
    assert record.line == line


@pytest.mark.parametrize("line", ["", " "])
def test_invalid_line(record, line):
    record.line = line
    assert "line" not in record.data


@pytest.mark.parametrize("ext", ["101", 102])
def test_ext(record, ext):
    record.ext = ext
    assert "ext" in record.data
    assert record.ext == ext


@pytest.mark.parametrize("ext", ["", " "])
def test_invalid_ext(record, ext):
    record.ext = ext
    assert "ext" not in record.data


@pytest.mark.parametrize("ring", ["20", 15, "00:15", "00:00:25"])
def test_ring(record, ring):
    record.ring = ring
    assert "ring" in record.data
    assert record.ring == ring


@pytest.mark.parametrize("ring", ["", " "])
def test_invalid_ring(record, ring):
    record.ring = ring
    assert "ring" not in record.data


@pytest.mark.parametrize("duration", ["200", 45, "00:56", "00:1:25"])
def test_duration(record, duration):
    record.duration = duration
    assert "duration" in record.data
    assert record.duration == duration


@pytest.mark.parametrize("duration", ["", " "])
def test_invalid_duration(record, duration):
    record.duration = duration
    assert "duration" not in record.data


@pytest.mark.parametrize("answered", ["true", "false", True, False, "1", "0", 1, 0])
def test_answered(record, answered):
    record.answered = answered
    assert "answered" in record.data
    assert record.answered == answered


@pytest.mark.parametrize("answered", ["", " "])
def test_invalid_answered(record, answered):
    record.answered = answered
    assert "answered" not in record.data
