Plugins
=======

Crreating Plugin
----------------

To create a plugin you first need to create a new module in the
plugins directory of the quartx_call_logger package.
Then create a class that inherits from either :class:`quartx_call_logger.plugins.Plugin` or
:class:`quartx_call_logger.plugins.SerialPlugin`.

There is one method that is required in the plugin class, "run".
This method is the main entry point for the plugin. This method should be
using a loop that checks the state of the plugin property ``sefl.running``, and
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

create documentation on how to do settings and how they are handeled and passed to the plugins.


Record API
----------

.. autoclass:: quartx_call_logger.record.Record



Plugin API
----------

.. autoclass:: quartx_call_logger.plugins.Plugin
    :members:
    :exclude-members: timeout, timeout_decay, max_timeout, logger

    .. attribute:: timeout
        :annotation: = 10

        The timeout setting in seconds

    .. attribute:: timeout_decay
        :annotation: = 1.5

        The timeout decay, used to increase the timeout after each failed connection

    .. attribute:: max_timeout
        :annotation: = 300

        The max timeout in seconds, the timeout will not decay past this point

    .. attribute:: logger
        :annotation: = logging.Logger

        The logger object associated with this plugin

.. autoclass:: quartx_call_logger.plugins.SerialPlugin
    :members:
    :exclude-members: run
