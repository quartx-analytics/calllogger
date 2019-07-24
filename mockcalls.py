# Standard library
import datetime
import random
import time

# Package
from call_logger import plugins
from call_logger.record import Record
from call_logger.__main__ import main


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
    def run(self):
        while self.running:
            if random.randrange(0, 2):
                # Incoming call
                number = number_gen()
                line = line_gen()
                ring = random.randrange(1, 25)
                ext = ext_gen()

                hops = int(ring / 4)
                for hop in range(hops):
                    ext = ext_gen()

                    self.push(Record(
                        Record.INCOMING,
                        #date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
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
                    #date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
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
                    #date=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    number=number_gen(),
                    line=line_gen(),
                    ext=ext_gen(),
                    ring=ring_gen(),
                    duration=duration,
                    answered=9 if not bool(duration) and random.randrange(1, 7) == 6 else int(bool(duration))
                ))

            # Sleep for a random time between 1 and 5 seconds
            time.sleep(0.1)


if __name__ == '__main__':
    main("Mockmonitor")
