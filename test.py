import time
from datetime import datetime
from influxdb_client import InfluxDBClient, Point

token = "rGZ5SNpn3GLYccWmMlR3xxEErUxji2b4oQB0AFTrcjuNklVt0CYuptpn4DKEYHjadHBJZzycL_B3aXEwGLQ6og=="
org = "quartx"
bucket = "temp"
measurement = "Pressure"

client = InfluxDBClient(url="https://influxdb.tools.quartx.dev", token=token, org=org)
write_api = client.write_api()
for i in range(10000):
    valOne = float(i)
    valTwo = float(i) + 0.5
    pointOne = Point(measurement).tag("sensor", "sensor1").field("PSI", valOne).time(time=datetime.utcnow())
    pointTwo = Point(measurement).tag("sensor", "sensor2").field("PSI", valTwo).time(time=datetime.utcnow())

    write_api.write(bucket, org, pointOne)
    write_api.write(bucket, org, pointTwo)
    print("PSI Readings: (%f, %f)" % (valOne, valTwo))
    time.sleep(0.5)

write_api.__del__()
