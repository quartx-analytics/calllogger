import pytest

from quartx_call_logger.record import Record


@pytest.fixture
def record():
    return Record(call_type=1, number="0876521354", line=1, ext=102, ring=10, duration=0)


def test_len(record):
    assert len(record) == 6


def test_contains(record):
    assert "ext" in record


def test_getitem(record):
    assert record["ext"] == 102


def test_get(record):
    assert record.get("ext") == 102
    assert record.get("ext2") is None


def test_setitem(record):
    record["ext"] = 103
    assert record["ext"] == 103


def test_delitem(record):
    assert "ext" in record
    del record["ext"]
    assert "ext" not in record


def test_iter(record):
    lst = list(iter(record))
    assert lst.sort() == ["call_type", "number", "line", "ext", "ring", "duration"].sort()


def test_clear(record):
    record.clear()
    assert len(record) == 0


def test_copy(record):
    new = record.copy()
    assert len(new) == 6


def test_items(record):
    assert len(record.items()) == 6


def test_keys(record):
    assert len(record.keys()) == 6


def test_values(record):
    assert len(record.values()) == 6


def test_pop(record):
    assert "ext" in record
    assert record.pop("ext", None)
    assert "ext" not in record


def test_popitem(record):
    record.popitem()
    assert len(record) == 5


def test_setdefault(record):
    assert record.setdefault("ext", 106) == 102
    assert record.setdefault("ext2", 106) == 106
    assert "ext2" in record


def test_update(record):
    record.update(ext=106)
    assert record["ext"] == 106
