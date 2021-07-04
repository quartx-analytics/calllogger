# Third Party
import pytest

# Local
from calllogger.influx import Point


@pytest.fixture
def point():
    return Point("test_metric")


@pytest.mark.parametrize("precision,length", [
    (Point.NANOSECONDS, 19),
    (Point.MICROSECONDS, 16),
    (Point.MILLISECONDS, 13),
    (Point.SECONDS, 10),
])
def test_time(point, precision, length):
    assert point._time is None
    point.time(precision)
    assert isinstance(point._time, int)
    assert len(str(point._time)) == length


def test_time_invalid(point: Point):
    assert point._time is None
    with pytest.raises(ValueError):
        point.time("invalid")


def test_set_tag(point: Point):
    assert not point._tags
    point.tag("tag", "value")
    assert point._tags.get("tag") == "value"


def test_set_tags(point: Point):
    assert not point._tags
    point.tags(tag1="value1", tag2="value2")
    assert point._tags.get("tag1") == "value1"
    assert point._tags.get("tag2") == "value2"


def test_set_field(point: Point):
    assert not point._fields
    point.field("field", "value")
    assert point._fields.get("field") == "value"


def test_set_fields(point: Point):
    assert not point._fields
    point.fields(field1="value1", field2="value2")
    assert point._fields.get("field1") == "value1"
    assert point._fields.get("field2") == "value2"


def test_line_protocol(point: Point):
    point.tag("tag", "value")
    point.field("field", "value")
    line = point.to_line_protocol()
    assert line == 'test_metric,tag=value field="value"'


def test_line_protocol_no_field(point: Point):
    point.tag("tag", "value")
    line = point.to_line_protocol()
    assert line == ''
