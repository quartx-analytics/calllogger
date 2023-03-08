[![tests](https://github.com/quartx-analytics/calllogger/actions/workflows/build-test.yml/badge.svg)](https://github.com/quartx-analytics/calllogger/actions/workflows/build-test.yml)
[![codecov](https://codecov.io/gh/quartx-analytics/calllogger/branch/master/graph/badge.svg?token=AH0TIQ7F8V)](https://codecov.io/gh/quartx-analytics/calllogger)
[![Maintainability](https://api.codeclimate.com/v1/badges/c0d513f139aa33e2d4b6/maintainability)](https://codeclimate.com/github/quartx-analytics/calllogger/maintainability)


Quartx Call Logger
==================

Call logger component for the Quartx phone system monitoring service. https://quartx.ie/

This logger can monitor phone systems for CDR(Call Data Records) and send the records to the monitoring service.
The monitoring frontend will then analyze the records and display them in a easy to view web interface.

Phone system support is done using plugins. The currently available plugins are:

* ``SiemensHipathSerial``: Add's support for the Siemens Hipath phone system, using the serial interface.
* ``Mock``: Generate random call records continuously.

This package is designed to be run within a containerized environment, for this we use docker.
The containerized image is built to work on linux/amd64 and linux/arm64.


Configuration
-------------

All the configuration is done through the docker command. Docker is configured through the command options and
the call logger is configured using environment variables.

Here is a list of command options that we will use to configure the docker container.

* ``--detach``: Tell docker to start in the background.
* ``--name "calllogger"``: Set the identifier name for the container.
* ``--volume="calllogger-data:/data"``: Create a docker data volume and mount it into the container,
  this is required as containers are stateless.
* ``--restart=on-failure``: Tell docker to start on startup and restart the docker container if
  the program exits unexpectedly.
* ``--network host``: Give the container direct access to the network devices. This is required
  for device identification.
* ``--env "KEY=VALUE"``: Set environment variables to be used by the call logger (Should not be needed).
* ``--device=/dev/ttyUSB0:/dev/ttyUSB0``: Mount the USB serial device into the container.
  The first path component is the path to the device on the host. The second path component is the mount point
  in the container. The call logger expects the device path to be ``/dev/ttyUSB0`` by default.
* ``--group-add dialout``: This will give the container permission to access a serial device.

If you do not need access to any serial device, you can omit the ``--device`` and ``--group-add`` parameters.

Below is a list of environment variables that can be used to configure the call logger. This is normally
controlled by the server, and is only used for testing.

* ``CHECKIN_INTERVAL``: Time between server checkins in minutes. Max 30min.
* ``TIMEOUT``: Timeout in seconds to sleep between errors.
* ``TIMEOUT_DECAY``: Multiplier that increases the timeout on continuous errors.
* ``MAX_TIMEOUT``: The max the timeout can be after continuous decay.
* ``QUEUE_SIZE``: Size of the call queue.
* ``DEBUG``: Set to ``true`` to enable debug logging.

Some plugins also have their own set of configurations that can be set using environment variables.

```bash
-e "PLUGIN_<SETTING>=<VALUE>"
```

Deployment
----------

There is only one command required to install, configure and run the call logger.
The plugin that will be used is determined by the server, but this can be overridden.

```bash
docker run --detach --name "calllogger" --device="/dev/ttyUSB0" --group-add dialout --volume="calllogger-data:/data" --restart=on-failure --network host ghcr.io/quartx-analytics/calllogger
```
