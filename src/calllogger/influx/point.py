from __future__ import annotations

# Standard Lib
from typing import Any

ESCAPE_MEASUREMENT = str.maketrans({
    ',': r'\,',
    ' ': r'\ ',
})

ESCAPE_KEY = str.maketrans({
    ',': r'\,',
    '=': r'\=',
    ' ': r'\ ',
})


class Point(object):
    """Point defines the values that will be written to the database."""

    def __init__(self, measurement_name):
        """Initialize defaults."""
        self._name = measurement_name
        self._time = None
        self._fields = {}
        self._tags = {}

    def tag(self, key: str, value: Any) -> Point:
        """Add tag with key and value."""
        self._tags[key] = value
        return self

    def tags(self, **kwargs: dict[str, Any]) -> Point:
        """Add tags with key and value."""
        self._tags.update(kwargs)
        return self

    def field(self, field: str, value: Any) -> Point:
        """Add field with key and value."""
        self._fields[field] = value
        return self

    def fields(self, **kwargs: dict[str, Any]) -> Point:
        """Add fields with key and value."""
        self._fields.update(kwargs)
        return self

    def to_line_protocol(self) -> str:
        """Create LineProtocol."""
        measurement = _translate_measurement(self._name)
        fields = _fields_protocol(self._fields)
        tags = _tags_protocol(self._tags)

        # No point in returning a line protocol if there is no fields
        if fields:
            return f"{measurement}{tags}{fields} {self._time}"
        else:
            return ""


def _tags_protocol(tags: dict[str, Any]) -> str:
    segments = []
    for key, value in sorted(tags.items()):
        # Influx don't care about empty tags
        if value is None:
            continue

        # We need to escape problematic characters
        tag = _translate_key(key)
        value = _translate_key(value)
        if tag and value:
            segments.append(f"{tag}={value}")

    return f"{',' if segments else ''}{','.join(segments)} "


def _fields_protocol(fields: dict[str, Any]) -> str:
    segments = []
    for key, value in sorted(fields.items()):
        # Influx don't care about empty fields
        if value is None:
            continue

        # InfluxDB assumes all numerical field values are floats.
        if isinstance(value, float):
            # It's common to represent whole numbers as floats
            # and the trailing ".0" that Python produces is unnecessary
            value = str(value)
            if value.endswith(".0"):
                value = value[:-2]

        # A lower case True/False will be stored as a boolean
        elif isinstance(value, bool):
            value = str(value).lower()

        # Append an i to the field value to tell InfluxDB to store the number as an integer
        elif isinstance(value, int):
            value = f"{value}i"

        # Double quote string field values
        elif isinstance(value, str):
            # Strip out any quotes, They are allowed but messy to work with
            value = value.replace('"', '').replace("'", "")
            value = f'"{value}"'
        else:
            raise ValueError(f'Type: "{type(value)}" of field: "{key}" is not supported.')

        # We need to escape problematic characters
        key = _translate_key(key)
        segments.append(f"{key}={value}")

    return f"{','.join(segments)}"


def _translate_measurement(value: Any) -> str:
    return str(value).strip().translate(ESCAPE_MEASUREMENT)


def _translate_key(value: Any) -> str:
    return str(value).strip().translate(ESCAPE_KEY)
