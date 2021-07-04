# Local
from calllogger.influx import Event, Counter, Gauge
from calllogger.metrics import collector


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
