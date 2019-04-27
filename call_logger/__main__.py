# Standard library
import argparse
import os

# Package imports
from call_logger import config, setup_env, reporter, arguments
from call_logger.monitors import monitor

# Create Parser to parse the required arguments
parser = argparse.ArgumentParser(description="Call logger")
for argument in arguments:
    parser.add_argument(*argument["args"], **argument["kwargs"])


def main():
    # Fetch authentication token from command line
    args = parser.parse_args()

    # Load the mocked monitor if required
    if args.simulate:
        if args.simulate is True:
            path = args.simulate
        else:
            path = os.path.realpath(os.path.expanduser(os.path.expandvars(args.simulate)))

        # Save the mock setting as a system
        config["settings"]["phone_system"] = "mockcalls"
        config["mockcalls"] = {"simulate": str(path), "delay": args.delay, "disable_incoming": args.disable_incoming}

    # Start the monitor script
    reporters = reporter.spawn_reporters()
    monitor(*reporters)


# Start the call monitoring software
if __name__ == '__main__':
    setup_env()
    main()
