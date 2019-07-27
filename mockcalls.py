"""
Call logger Mocker

positional arguments:
  token                 The token that is used to authenticate with the
                        monitoring server.

optional arguments:
  -h, --help            show this help message and exit
  -f FRONTEND, --frontend FRONTEND
                        The uri for the server e.g. 'http://127.0.0.1:8080',
                        defaults to 'https://quartx.ie/'
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
from urllib import parse as urlparse

# Package
from quartx_call_logger import plugins, api
from quartx_call_logger.record import Record


# Create Parser to parse the required arguments
parser = argparse.ArgumentParser(description="Call logger")
parser.add_argument(
    "token",
    help="The required token used to authenticate with the monitoring server."
)
parser.add_argument(
    "-f",
    "--frontend",
    help="The uri for the server e.g. 'http://127.0.0.1:8000', defaults to 'https://quartx.ie/.'",
    default="https://quartx.ie/"
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
    ran = random.randrange(3)
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
        num = random.randrange(0, len(common_custumors))
        return "+353%s" % common_custumors[num]

    # 2 in 3 chance its a random customer
    elif ran == 1:
        # random mobile numbers
        prefix = random.randrange(85, 87)
        num = random.randrange(1000000, 9999999)
        return "+353{}{}".format(prefix, num)

    else:
        # random landline numbers
        prefix = random.randrange(10, 90)
        num = random.randrange(1000000, 9999999)
        return "+353{}{}".format(prefix, num)


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
    def __init__(self, delay: int, **kwargs):
        super(Mockmonitor, self).__init__(**kwargs)
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
                            Record.INCOMING,
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
                    Record.RECEIVED,
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
                    Record.OUTGOING,
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


if __name__ == '__main__':
    # Fetch authentication token from command line
    args = parser.parse_args()

    # Set the api token
    api.token = args.token

    # Set the api url
    base = urlparse.urlsplit(api.url)
    new = urlparse.urlsplit(args.frontend)
    api.url = urlparse.urlunsplit((new.scheme, new.netloc, base.path, base.query, base.fragment))

    # Start the plugin
    plugin = Mockmonitor(args.slow_mode)
    plugin.start()
