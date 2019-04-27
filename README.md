# Call Logger

This script monitors a phone system for calls and logs incomming and outgoing calls.
All call logs are then farwarded on to a call monitoring frontend for remote viewing.

The supported phone systems are:
* Siemens Hipath (using the serial interface)

## Installation

```{.sourceCode .bash}
$ pip install https://github.com/callmonitoring/call_logger/archive/master.zip
```

## Documentation
When starting call-logger for the first time, you need to pass in the
authentication Token that is required to comunicate with the frontend.
The Token will then be encripted and store for later use.
```{.sourceCode .bash}
$ python -m call-logger --key 3215eseffsf58165dfdsw848432685a48d32f1w84s3d2fw
```
---
The config file will be located in the users config directory.
Please make your changes as required.

Linux:
```
/home/${USER}/.config/call-logger/config.ini
```

Windows:
```
C:\Users\${USER}\AppData\Local\call-logger\config.ini
```
