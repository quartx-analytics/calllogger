# Standard lib
import queue

# Local
from calllogger.telemetry.instruments import Metric, Event, Counter, Gauge, Histogram
from calllogger.telemetry.collectors import InfluxCollector
from calllogger.telemetry import collector


def test_metric():
    metric = Metric("event_metric", collector)
    queue_count = collector.queue.qsize()

    metric.field("value", True).write()
    line = metric.to_line_protocol()
    assert line.startswith("event_metric value=true")
    assert collector.queue.qsize() == queue_count + 1


def test_metric_none():
    metric = Metric("event_metric", collector)
    queue_count = collector.queue.qsize()

    metric.field("value", None).write()
    line = metric.to_line_protocol()
    assert line == ""
    # Metric queue should not have increased as the line should be ignored
    assert collector.queue.qsize() == queue_count


def test_metric_queue_full(mocker):
    mocked_q = mocker.patch.object(queue, "SimpleQueue")
    new_collector = InfluxCollector("", "")
    metric = Metric("event_metric", new_collector)
    mocked_q.return_value.qsize.return_value = 1_001
    metric.field("value", True).write()


def test_event():
    event = Event("event_metric", collector)
    queue_count = collector.queue.qsize()

    event.mark()
    line = event.to_line_protocol()
    assert line.startswith("event_metric value=true")
    assert collector.queue.qsize() == queue_count + 1


def test_counter():
    counter = Counter("counter_metric", collector)
    queue_count = collector.queue.qsize()

    # First count should be 1
    counter.inc()
    line = counter.to_line_protocol()
    assert line.startswith("counter_metric value=1i")
    assert collector.queue.qsize() == queue_count + 1

    # Second call should report 2
    counter.inc()
    line = counter.to_line_protocol()
    assert line.startswith("counter_metric value=2i")
    assert collector.queue.qsize() == queue_count + 2


def test_gauge():
    gauge = Gauge("gauge_metric", collector)
    queue_count = collector.queue.qsize()

    # Should be set the 10
    gauge.set(10)
    line = gauge.to_line_protocol()
    assert line.startswith("gauge_metric value=10i")
    assert collector.queue.qsize() == queue_count + 1

    # Should be increased to 11
    gauge.inc()
    line = gauge.to_line_protocol()
    assert line.startswith("gauge_metric value=11i")
    assert collector.queue.qsize() == queue_count + 2

    # Should should be decreased to 10
    gauge.dec()
    line = gauge.to_line_protocol()
    assert line.startswith("gauge_metric value=10i")
    assert collector.queue.qsize() == queue_count + 3


def test_histogram():
    histogram = Histogram("event_metric", collector)
    queue_count = collector.queue.qsize()

    histogram.observe(0.052)
    line = histogram.to_line_protocol()
    assert line.startswith("event_metric value=0.052")
    assert collector.queue.qsize() == queue_count + 1
