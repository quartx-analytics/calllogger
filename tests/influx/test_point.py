# Third Party
import pytest

# Local
from calllogger.metrics.point import Point


@pytest.fixture
def point():
    return Point("test_metric")


@pytest.mark.parametrize("precision,length", [
    (Point.NANOSECONDS, 19),
    (Point.MICROSECONDS, 16),
    (Point.MILLISECONDS, 13),
    (Point.SECONDS, 10),
])
def test_time(point: Point, precision, length):
    """Test that time will be set to the correct precision."""
    assert point._time is None
    ret = point.time(precision)
    assert isinstance(ret, Point)
    assert isinstance(point._time, int)
    assert len(str(point._time)) == length


def test_time_invalid(point: Point):
    """Test that an invalid precision value raises a ValueError."""
    assert point._time is None
    with pytest.raises(ValueError):
        point.time("invalid")


def test_set_tag(point: Point):
    """Test that point.tag works as expected."""
    assert not point._tags
    ret = point.tag("tag", "value")
    assert isinstance(ret, Point)
    assert point._tags.get("tag") == "value"


def test_set_tags(point: Point):
    """Test that point.tags works as expected."""
    assert not point._tags
    ret = point.tags(tag1="value1", tag2="value2")
    assert isinstance(ret, Point)
    assert point._tags.get("tag1") == "value1"
    assert point._tags.get("tag2") == "value2"


def test_set_field(point: Point):
    """Test that point.field works as expected."""
    assert not point._fields
    ret = point.field("field", "value")
    assert isinstance(ret, Point)
    assert point._fields.get("field") == "value"


def test_set_fields(point: Point):
    """Test that point.fields works as expected."""
    assert not point._fields
    ret = point.fields(field1="value1", field2="value2")
    assert isinstance(ret, Point)
    assert point._fields.get("field1") == "value1"
    assert point._fields.get("field2") == "value2"


def test_line_protocol(point: Point):
    """Test that the line protocol output is as expected."""
    point.tag("tag", "value")
    point.field("field", "value")
    line = point.to_line_protocol()
    assert line == 'test_metric,tag=value field="value"'


def test_line_protocol_no_field(point: Point):
    """That that a point with no field outputs an empty line."""
    point.tag("tag", "value")
    line = point.to_line_protocol()
    assert line == ''


def test_none_value(point: Point):
    """Test that tags & fields ignore value of type None."""
    point.tag("tag1", "value")
    point.tag("tag2", None)
    point.field("field1", "value")
    point.field("field2", None)
    line = point.to_line_protocol()
    assert line == 'test_metric,tag1=value field1="value"'


@pytest.mark.parametrize("value,expected_line", [
    (10.1, "test_metric field=10.1"),
    (10.0, "test_metric field=10"),
    (True, "test_metric field=true"),
    (False, "test_metric field=false"),
    (0, "test_metric field=0i"),
    (5, "test_metric field=5i"),
    ("value", 'test_metric field="value"'),
])
def test_field_value_types(point: Point, value, expected_line):
    """Test different value type get converted to the right format."""
    point.field("field", value)
    line = point.to_line_protocol()
    assert line == expected_line


def test_invalid_field_type(point: Point):
    """Test that an unsupported value type raises ValueError."""
    point.field("field", object())
    with pytest.raises(ValueError):
        point.to_line_protocol()
