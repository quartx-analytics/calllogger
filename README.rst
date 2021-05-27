.. image:: https://github.com/quartx-analytics/calllogger/actions/workflows/build-test.yml/badge.svg
    :target: https://github.com/quartx-analytics/calllogger/actions/workflows/build-test.yml
    :alt: Build and Tests

.. image:: https://codecov.io/gh/quartx-analytics/calllogger/branch/master/graph/badge.svg?token=AH0TIQ7F8V
    :target: https://codecov.io/gh/quartx-analytics/calllogger
    :alt: Test Coverage

.. image:: https://api.codeclimate.com/v1/badges/c0d513f139aa33e2d4b6/maintainability
   :target: https://codeclimate.com/github/quartx-analytics/calllogger/maintainability
   :alt: Maintainability


Quartx Call Logger
------------------

Call logger component for the Quartx phone system monitoring service. https://quartx.ie/

This logger can monitor phone systems for CDR(Call Data Records) and send the records to the monitoring service.
The monitoring frontend will then analyze the records and display them in a easy to view web interface.

The currently supported phone systems are:

    * Siemens Hipath


Deployment
----------

This package is designed to be run within a containerized environment, for this we can use docker.
The containerized image is built to work on linux/amd64, linux/arm64, linux/arm/v7.
Configuration is done through environment variables, currently only two are required.

    * **TOKEN**: Authentication key used to identify who owns the call logs.
    * **PLUGIN**: The plugin to use. For now this will be ``SiemensHipathSerial``.

The Siemens Hipath plugin accesses the phone system using the serial interface.
The serial interface needs to be passed to the docker container using the ``--device`` option in docker.

There is only one command required to install, configure and run the call logger.
Don't forget to change the ``token`` to the required value. Also make sure that the device path is correct.

.. code-block:: bash

    docker run --detach --name "calllogger" -e "TOKEN=<token>" -e "PLUGIN=SiemensHipathSerial" --device=/dev/ttyUSB0:/dev/ttyUSB0 --volume="calllogger-data:/data" --restart=on-failure --network host ghcr.io/quartx-analytics/calllogger
