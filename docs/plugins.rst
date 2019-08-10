Plugins
=======

Crreating Plugin
----------------

To create a plugin you first need to create a new module in the
plugins directory of the quartx_call_logger package.
Then create a class that inherits from either :class:`quartx_call_logger.plugins.Plugin` or
:class:`quartx_call_logger.plugins.SerialPlugin`.
When the call logger start up it scans for the plugin directory for plugins and registors them automatically.

There is one method that is required in the plugin class, "run".
This method is the main entry point for the plugin. This method should be
using a loop that checks the state of the plugin property ``self.running``, and
when true the loop should continue monitoring the call logs.

.. code-block:: python

    from . import Plugin, Record

    class VoipService(Plugin):
        def run(self):
            while self.running:
                # Run code that monitors for call logs
                ...

                # Create a call record
                record = Record(Record.INCOMING, number="0876156584", line=2, ext=101)

                # Send the call record to the monitoring frontend
                self.push(record)


Settings
--------

If there are any required settings for the plugin, they should be added to the defaults.yml configuration file.
This file is located in ``/quartx_call_logger/data/defaults.yml``. These settings are then passed to the plugin
constructor whenever the plugin is initialized.

Example settings configuration::

    SiemensHipathSerial:
      # Port & baud rate settings required to communicate with the Siemen Hipath serial interface
      # port: The port where the serial device is located. e.g. /dev/ttyUSB0 on GNU/Linux or COM3 on Windows
      # rate: Baud rate used when communicating with the serial interface, such as 9600
      port: /dev/ttyUSB0
      rate: 9600

.. note:: The name for the plugin settings need to be the exact name given to the plugin class


Record API
----------

.. autoclass:: quartx_call_logger.record.Record



Plugin API
----------

.. autoclass:: quartx_call_logger.plugins.Plugin()
    :members:
    :exclude-members: timeout, timeout_decay, max_timeout, logger

    .. attribute:: timeout
        :annotation: = 10

        The timeout setting in seconds. Can be changed in the user config.

    .. attribute:: timeout_decay
        :annotation: = 1.5

        The timeout decay, used to increase the timeout after each failed connection. Can be changed in the user config.

    .. attribute:: max_timeout
        :annotation: = 300

        The max timeout in seconds, the timeout will not decay past this point. Can be changed in the user config.

    .. attribute:: base_timeout
        :annotation: = 10

        The base timeout value without decay

    .. attribute:: logger
        :annotation: = logging.Logger

        The logger object associated with this plugin

.. autoclass:: quartx_call_logger.plugins.SerialPlugin
    :members:
    :exclude-members: run
