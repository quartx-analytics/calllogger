.. image:: https://api.codacy.com/project/badge/Grade/af3dc404e10e4a8f9f8e79823ff654e9
    :target: https://www.codacy.com/app/Quartx/quartx-call-logger?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=quartx-software/quartx-call-logger&amp;utm_campaign=Badge_Grade

.. image:: https://travis-ci.org/quartx-software/quartx-call-logger.svg?branch=master
    :target: https://travis-ci.org/quartx-software/quartx-call-logger

.. image:: https://coveralls.io/repos/github/quartx-software/quartx-call-logger/badge.svg?branch=master
    :target: https://coveralls.io/github/quartx-software/quartx-call-logger?branch=master


Quartx Call Logger
------------------

Call logger component for the Quartx phone system monitoring frontend.
http://www.quartx.ie/


Install
-------

There are two ways to install this package. First is by using PYPI to install system wide, the other is by cloning
the git repo and install using Pipenv to isolate the package from the rest of the system for development.

Production ::

    pip install quartx_call_logger

Development ::

    git clone https://github.com/quartx-software/quartx-call-logger.git
    cd quartx-call-logger
    pip install pipenv
    pipenv install --dev


Configuration
-------------

The Configuration for this package is located in ``/Library/Application Support/quartx`` on MacOS,
``/etc/xdg/quartx`` on Unix systems or ``C:\ProgramData\quartx\quartx`` on Windows.

First we download the base configuration file from github so we can modifiy it. The following commands are for Linux/Unix.
::

    sudo mkdir -p /etc/xdg/quartx
    sudo curl https://raw.githubusercontent.com/quartx-software/quartx-call-logger/master/quartx_call_logger/data/default.yml > /etc/xdg/quartx/call-logger.yml

At the moment only one setting is required to be set by the user, that is the ``token``.
The token is the authentication key used to authenticate the user and identify who the call logs belong to.
Contact Quartx Call Monitoring for the token key.
::

    sudo nano /etc/xdg/quartx/call-logger.yml
    ...
    token: 3bf6940a6bc249a729e7e4fdd5350bb4887d2dac942a553b198f2dfc678055bf
    ...

If running under Linux then the systemd unit file should be installed.
::

    sudo curl https://raw.githubusercontent.com/quartx-software/quartx-call-logger/master/quartx-call-logger.service > /etc/systemd/system/call-logger.service


Usage
-----

The call logger can be run with just one single command when on Linux.
::

    call-logger
