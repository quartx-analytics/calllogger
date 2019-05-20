# Standard library
import threading
import functools
import datetime
import queue
import os

# Django
from django.core.management.base import BaseCommand

# Package
from call_frontend import models
from call_logger import logger, plugins, config, reporter, setup_env, arguments
from call_logger.monitors import monitor


class DirectReporter(threading.Thread):
    def __init__(self, user, call_queue: queue.Queue):
        super().__init__()
        self.calls = call_queue
        self.user = user

    def run(self):
        """Continuously check the call queue for new records to process."""
        while True:
            # Fetch the call record from the queue
            record: plugins.Call = self.calls.get().copy()

            try:
                # Get or create object instances
                contact = self.get_contact(record.pop("number"))
                ext = self.get_ext(self.user, record.pop("ext"))

                # Log a active incoming call
                if record.call_type == plugins.INCOMING:
                    self.create_incoming(site=self.user, contact=contact, ext=ext, **record)
                else:
                    # Log a outgoing or received call
                    ring = datetime.timedelta(seconds=record.pop("ring"))
                    duration = datetime.timedelta(seconds=record.pop("duration"))
                    self.create_call(site=self.user, contact=contact, ext=ext, ring=ring, duration=duration, **record)

            except Exception as e:
                logger.error(f"Failed to create database entry for: {record}")
                logger.exception(e)

            # Record has been logged
            self.calls.task_done()

    # noinspection PyUnresolvedReferences
    @staticmethod
    def create_incoming(**record):
        """Log that an incoming call is active."""
        try:
            # Check if this incoming call already exists
            # This is very usefull, it makes it a lot easir for the call logger to update the incoming table
            instance = models.Incoming.objects.get(site=record["site"], contact=record["contact"])
        except models.Incoming.DoesNotExist:
            # Just call the original create method
            models.Incoming.objects.create(**record)
        else:
            # Update the pre existing instance instead of creating a new one
            instance.ext = record["ext"]
            instance.line = record["line"]
            instance.save()

    @staticmethod
    def create_call(**record):
        """Log that a there was a outgoing or received call logged."""
        models.Call.objects.create(**record)

    @staticmethod
    def get_contact(number):
        """Return a Contact instance for given number. Creating one if don't exist."""
        ins, _ = models.Contact.objects.get_or_create(number=number)
        return ins

    @staticmethod
    def get_ext(site, ext):
        """Return a Ext instance for the given site & ext. Creating one if don't exist."""
        ins, _ = models.Ext.objects.get_or_create(site=site, ext=ext)
        return ins


class Command(BaseCommand):
    help = "Clear out all stale incoming call records."

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("user")
        parser.add_argument(
            "-f",
            "--enable-frontends",
            action="store_true",
            help="Send call logs to frontend as well as direct."
        )
        for argument in arguments:
            parser.add_argument(*argument["args"], **argument["kwargs"])

    def handle(self, *args, **options):
        setup_env()

        # Fetch the user instance
        user = self.get_user(options["user"])
        self.cleanup()

        # Load the mocked monitor if required
        if "simulate" in options and options["simulate"]:
            if options["simulate"] is True:
                path = options["simulate"]
            else:
                path = os.path.realpath(os.path.expanduser(os.path.expandvars(options["simulate"])))

            # Save the mock setting as a system
            config["settings"]["phone_system"] = "mockcalls"
            config["mockcalls"] = {"simulate": str(path), "delay": options.get("delay", 2),
                                   "disable_incoming": options.get("disable_incoming")}

        direct_reporter = functools.partial(DirectReporter, user)
        if "enable_frontends" in options and options["enable_frontends"]:
            reporters = reporter.spawn_reporters()
            monitor(direct_reporter, *reporters)
        else:
            monitor(direct_reporter)

    def cleanup(self):
        models.Incoming.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Successfully cleaned incoming"))

    # noinspection PyUnresolvedReferences
    @staticmethod
    def get_user(username):
        try:
            return models.User.objects.get(username=username)
        except models.User.DoesNotExist:
            logger.error(f"User \"{username}\" not found")
            exit(1)
