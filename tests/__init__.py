import os

# Test Defaults
defaults = dict(
    token="temp",
    plugin="MockCalls",
)

# Add test defaults to environment
for key, val in defaults.items():
    if key not in os.environ:
        os.environ[key.upper()] = val
