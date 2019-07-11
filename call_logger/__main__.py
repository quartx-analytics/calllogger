# Package imports
from call_logger import setup_env, reporter
from call_logger.monitors import monitor


def main():
    # Start the monitor script
    reporters = reporter.spawn_reporters()
    monitor(*reporters)


# Start the call monitoring software
if __name__ == '__main__':
    setup_env()
    main()
