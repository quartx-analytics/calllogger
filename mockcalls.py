"""
Call logger Mocker

positional arguments:
  token                 The token that is used to authenticate with the
                        monitoring server.

optional arguments:
  -h, --help            show this help message and exit
  -d DOMAIN, --domain DOMAIN
                        The domain of the server e.g. '127.0.0.1:8080' or 'quartx.ie',
                        defaults to 'stage.quartx.ie'.
  -s [1], --slow-mode [1]
                        Slow down the rate of mocked calls.

# To send mock calls as fast as posible
python mockcalls.py 2165432165432df654d854e3241efsfsd32485 -f http://127.0.0.1:8000/

# To send mock calls at a more normal rate, including incoming calls
python mockcalls.py 2165432165432df654d854e3241efsfsd32485 -f http://127.0.0.1:8000/ -s 3
"""

# Standard library
# import datetime
import argparse
import random
import time

# Phonenumbers
import phonenumbers

# Package
from quartx_call_logger import plugins, settings
from quartx_call_logger.record import Record


# Create Parser to parse the required arguments
parser = argparse.ArgumentParser(description="Call logger")
parser.add_argument(
    "token",
    help="The required token used to authenticate with the monitoring server."
)
parser.add_argument(
    "-d",
    "--domain",
    help="The domain of the server e.g. '127.0.0.1:8080' or 'quartx.ie', defaults to 'stage.quartx.ie'.",
    default="stage.quartx.ie"
)
parser.add_argument(
    "-l",
    "--no-ssl",
    action="store_false",
    help="Disable SSL mode (https)."
)
parser.add_argument(
    "-v",
    "--no-verify",
    action="store_false",
    help="Disable SSL verification."
)
parser.add_argument(
    "-s",
    "--slow-mode",
    nargs="?",
    type=int,
    const=1,
    default=0,
    metavar="1",
    help="Slow down the rate of mocked calls. This also enables incoming call logs."
)


def number_gen():
    """Generate a random phone number"""
    ran = random.randrange(5)
    # 1 in 3 chance its a regular customar
    if ran == 0:
        common_custumors = [
            '857739075',  # Michael Forde
            '873565643',  # Tom Baker
            '853435640',  # Jerry Cremin
            '277663604',  # Louie Walsh
            '107975846',  # Tim Barra
            '213265621',  # Mike Twomey
            '850546045',  # Philip Murray
            '877640458',  # Maura Jenkins
        ]
        return "+353{}".format(random.choice(common_custumors))

    while True:
        # 2 in 3 chance its a random customer
        if ran == 1:
            number_type = phonenumbers.PhoneNumberType.MOBILE
        elif ran == 2:
            number_type = phonenumbers.PhoneNumberType.VOIP
        else:
            number_type = phonenumbers.PhoneNumberType.FIXED_LINE

        num_obj = phonenumbers.example_number_for_type("IE", number_type)
        if phonenumbers.is_valid_number(num_obj):
            return phonenumbers.format_number(num_obj, phonenumbers.PhoneNumberFormat.E164)


def ext_gen():
    """Generate a random ext number"""
    return random.randrange(100, 110)


def line_gen():
    """Generate a random line number"""
    return random.randrange(1, 4)


def duration_gen():
    """One in five chance of not been answered"""
    return 0 if random.randrange(5) == 0 else random.randrange(0, 10000)


def ring_gen():
    """Generate a random ring time"""
    return random.randrange(1, 100)


class Mockmonitor(plugins.Plugin):
    def __init__(self, delay: int):
        super(Mockmonitor, self).__init__()
        self.delay = delay

    def run(self):
        while self.running:
            if random.randrange(0, 2):
                # Incoming call
                number = number_gen()
                line = line_gen()
                ring = random.randrange(1, 20)
                ext = ext_gen()

                if self.delay:
                    hops = int(ring / 4)
                    for hop in range(hops):
                        ext = ext_gen()

                        self.push(Record(
                            call_type=Record.INCOMING,
                            # date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            number=number,
                            line=line,
                            ext=ext
                        ))
                        time.sleep(hop)

                duration = duration_gen()
                answered = int(bool(duration))

                # One if 4 change of been answered by voicmail
                if answered and random.randrange(1, 5) == 1:
                    answered = Record.VOICEMAIL
                    ext = 200

                self.push(Record(
                    call_type=Record.RECEIVED,
                    # date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    number=number,
                    ext=ext,
                    line=line,
                    ring=ring,
                    duration=duration,
                    answered=answered
                ))

            else:
                duration = duration_gen()
                self.push(Record(
                    call_type=Record.OUTGOING,
                    # date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    number=number_gen(),
                    line=line_gen(),
                    ext=ext_gen(),
                    ring=ring_gen(),
                    duration=duration,
                    answered=int(bool(duration))
                ))

            # Sleep for a random time between 1 and 5 seconds
            time.sleep(self.delay)

    def push(self, record: Record):
        print(record)
        super(Mockmonitor, self).push(record)


if __name__ == '__main__':
    # Fetch authentication token from command line
    args = parser.parse_args()
    settings.set_token(args.token)
    settings.DOMAIN = args.domain

    # Start the plugin
    plugin = Mockmonitor(args.slow_mode)
    plugin.start()
