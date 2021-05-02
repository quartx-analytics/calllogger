import os

# Test Defaults
defaults = dict(
    token="temp",
    plugin="MockCalls",
)

# TODO: Find a better fix for this. This breaks in pytest with --import-mode=importlib
# Add test defaults to environment
for key, val in defaults.items():
    if key not in os.environ:
        os.environ[key.upper()] = val
