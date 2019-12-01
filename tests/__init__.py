import os

# Disable sentry logging for tests
os.environ["DISABLE_SENTRY"] = "1"
