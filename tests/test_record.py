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
    record = CallDataRecord(0)
    record.call_type = call_type
    assert record.call_type == call_type


def test_date_obj(record):
    date = datetime.now(timezone.utc).replace(microsecond=0)
    record.date = date
    assert "date" in record.as_dict()
    assert record.date == date


def test_date_str(record):
    fmt = "%d.%m.%y%X"
    tz = timezone.utc
    date = datetime.now(timezone.utc).replace(microsecond=0)
    record.date_str(date.strftime(fmt), fmt=fmt, tz=tz)
    assert "date" in record.as_dict()
    assert record.date == date


@pytest.mark.parametrize("date", ["", " "])
def test_invalid_date(record, date):
    before = record.date
    record.date_str(date)
    assert record.date == before


@pytest.mark.parametrize("number", ["0876159281", "066715325", "", None])
def test_number(record, number):
    record.number = number
    assert "number" in record.as_dict()
    assert record.number == number


@pytest.mark.parametrize("contact_name", ["contact", "name", "", None])
def test_contact_name(record, contact_name):
    record.contact_name = contact_name
    assert "contact_name" in record.as_dict()
    assert record.contact_name == contact_name


@pytest.mark.parametrize("contact_email", ["contact", "email@email.com", "", None])
def test_contact_email(record, contact_email):
    record.contact_email = contact_email
    assert "contact_email" in record.as_dict()
    assert record.contact_email == contact_email


@pytest.mark.parametrize("line", ["1", 2, "", None])
def test_line(record, line):
    record.line = line
    assert "line" in record.as_dict()
    assert record.line == line


@pytest.mark.parametrize("ext", ["101", 102, "", None])
def test_ext(record, ext):
    record.ext = ext
    assert "ext" in record.as_dict()
    assert record.ext == ext


@pytest.mark.parametrize("ext_name", ["extension", "name", "", None])
def test_ext_name(record, ext_name):
    record.ext_name = ext_name
    assert "ext_name" in record.as_dict()
    assert record.ext_name == ext_name


@pytest.mark.parametrize("ring", ["20", 15, "00:15", "00:00:25", "", None])
def test_ring(record, ring):
    record.ring = ring
    assert "ring" in record.as_dict()
    assert record.ring == ring


@pytest.mark.parametrize("duration", ["200", 45, "00:56", "00:1:25", "", None])
def test_duration(record, duration):
    record.duration = duration
    assert "duration" in record.as_dict()
    assert record.duration == duration


@pytest.mark.parametrize("answered", ["true", "false", True, False, "1", "0", 1, 0, "", None])
def test_answered(record, answered):
    record.answered = answered
    assert "answered" in record.as_dict()
    assert record.answered == answered
