# Standard library
import datetime
import random
import time
import json

# Package import
from .. import logger, config, plugins


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


@plugins.register
class Mockmonitor(plugins.BasePlugin):
    name = "mockcalls"

    def __init__(self, call_queue, *args, **kwargs):
        super(Mockmonitor, self).__init__(*args, **kwargs)
        simulator = config["mockcalls"]["simulate"]
        self.delay = config["mockcalls"].getfloat("delay", 1)
        self.disable_incoming = config["mockcalls"].getboolean("disable_incoming", False)
        self.queue = call_queue

        try:
            # Continuous simulation until user quits
            for call in (self.live() if simulator.lower() == "true" else self.repeat_data(simulator)):
                call_queue.put(call)
                logger.info(call)

        except KeyboardInterrupt:
            pass

    def live(self):
        while True:
            if random.randrange(0, 2):
                # Incoming call
                number = number_gen()
                line = line_gen()
                ring = random.randrange(1, 25)
                ext = ext_gen()

                if self.disable_incoming is False:
                    hops = int(ring / 4) + 1  # 2 is the time in seconds before the call jumps to next ext
                    for hop in range(hops):
                        ext = ext_gen()

                        yield plugins.Call(
                            plugins.INCOMING,
                            number=number,
                            line=line,
                            ext=ext
                        )
                        time.sleep(hop)

                duration = duration_gen()
                answered = int(bool(duration))

                # One if 4 change of been answered by voicmail
                if answered and random.randrange(1, 5) == 1:
                    answered = plugins.VOICEMAIL
                    ext = 200

                yield plugins.Call(
                    plugins.RECEIVED,
                    date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    number=number,
                    ext=ext,
                    line=line,
                    ring=ring,
                    duration=duration,
                    answered=answered
                )

            else:
                duration = duration_gen()
                yield plugins.Call(
                    plugins.OUTGOING,
                    date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    number=number_gen(),
                    line=line_gen(),
                    ext=ext_gen(),
                    ring=ring_gen(),
                    duration=duration,
                    answered=9 if not bool(duration) and random.randrange(1, 7) == 6 else int(bool(duration))
                )

            # Sleep for a random time between 1 and 5 seconds
            if self.delay:
                time.sleep(self.delay)

    def repeat_data(self, path):
        """
        Local mock data from json file.

        Example:
            [
                [0, {"number": "0248873711", "line": 3, "ext": 48}],
                [1, {"number": "0248873711", "line": 3, "ext": 48, "ring": 41, "duration": 603, "answered": 1}],
                [2, {"number": "0922735086", "line": 3, "ext": 58, "ring": 7, "duration": 0, "answered": 0}]
            ]
        """

        with open(path, "r") as stream:
            data = json.load(stream)

        for call_type, call in data:
            call["number"] = call["number"]
            yield plugins.Call(call_type, **call)
            if self.delay:
                time.sleep(self.delay)

        logger.info("Waiting on call logs to be sent to frontend...")
        self.queue.join()
