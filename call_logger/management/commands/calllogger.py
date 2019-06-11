# Standard library
import threading
import functools
import datetime
import queue
import os

# Django
from django.core.management.base import BaseCommand

# Package
from call_frontend import models, utils
from call_logger import logger, plugins, config, reporter, setup_env, arguments
from call_logger.monitors import monitor


class DirectReporter(threading.Thread):
    def __init__(self, tenant, call_queue: queue.Queue):
        super().__init__()
        self.calls = call_queue
        self.tenant = tenant

    def run(self):
        """Continuously check the call queue for new records to process."""
        while True:
            # Fetch the call record from the queue
            record: plugins.Call = self.calls.get().copy()

            try:
                # Get or create object instances
                contact = self.get_contact(self.tenant, record.pop("number"))
                ext = self.get_ext(self.tenant, record.pop("ext"))

                # Log a active incoming call
                if record.call_type == plugins.INCOMING:
                    self.create_incoming(tenant=self.tenant, contact=contact, ext=ext, **record)
                else:
                    # Log a outgoing or received call
                    ring = datetime.timedelta(seconds=record.pop("ring"))
                    duration = datetime.timedelta(seconds=record.pop("duration"))
                    self.create_call(
                        tenant=self.tenant,
                        contact=contact,
                        ext=ext,
                        ring=ring,
                        duration=duration,
                        **record
                    )

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
            instance = models.Incoming.all_objects.get(tenant=record["tenant"], contact=record["contact"])
        except models.Incoming.DoesNotExist:
            # Just call the original create method
            models.Incoming.all_objects.create(**record)
        else:
            # Update the pre existing instance instead of creating a new one
            instance.ext = record["ext"]
            instance.line = record["line"]
            instance.save()

    @staticmethod
    def create_call(**record):
        """Log that a there was a outgoing or received call logged."""
        callobj = models.Call.all_objects.create(**record)
        
        if callobj.answered == models.Call.ANSWERED:
            # Remove call from missed if caller
            # called back after an unanswered call
            models.Missed.all_objects.filter(tenant=callobj.tenant, call__contact=callobj.contact).delete()

            # Also remove call log from callback table
            models.Callback.all_objects.filter(tenant=callobj.tenant, contact=callobj.contact).delete()

        if callobj.call_type == models.Call.RECEIVED:
            # Remove call from incomming if call was received
            models.Incoming.all_objects.filter(tenant=callobj.tenant, contact=callobj.contact).delete()

            # Log that a call was missed if call was not answered
            if callobj.answered == models.Call.NOT_ANSWERED or callobj.answered == models.Call.VOICEMAIL:
                models.Missed(tenant=callobj.tenant, call=callobj).save()

    @staticmethod
    def get_contact(tenant, number):
        """Return a Contact instance for given number. Creating one if don't exist."""
        number = utils.Phonenumbers(number)
        ins, _ = models.Contact.all_objects.only("id").get_or_create(tenant=tenant, number=number.as_e164)
        return ins

    @staticmethod
    def get_ext(tenant, ext):
        """Return a Ext instance for the given site & ext. Creating one if don't exist."""
        ins, _ = models.Ext.all_objects.only("id").get_or_create(tenant=tenant, ext=ext)
        return ins


class Command(BaseCommand):
    help = "Clear out all stale incoming call records."

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument("tenant")
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
        tenant = self.get_tenant(options["tenant"])
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

        direct_reporter = functools.partial(DirectReporter, tenant)
        if "enable_frontends" in options and options["enable_frontends"]:
            reporters = reporter.spawn_reporters()
            monitor(direct_reporter, *reporters)
        else:
            monitor(direct_reporter)

    def cleanup(self):
        models.Incoming.all_objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Successfully cleaned incoming"))

    # noinspection PyUnresolvedReferences
    @staticmethod
    def get_tenant(tenant):
        try:
            return models.Tenant.objects.only("id").get(name=tenant)
        except models.User.DoesNotExist:
            logger.error(f"Tenant \"{tenant}\" not found")
            exit(1)
