import os

# Test Defaults
defaults = dict(
    debug=0,
    collect_logs=0,
    collect_metrics=0,
    sentry_dsn="",
)

# TODO: Find a better fix for this. This breaks in pytest with --import-mode=importlib
# Add test defaults to environment
for key, val in defaults.items():
    if key not in os.environ:
        os.environ[key.upper()] = str(val)
