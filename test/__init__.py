import os

# Test Defaults
defaults = dict(
    TOKEN="temp",
)

# Add test defaults to environment
for key, val in defaults.items():
    if key not in os.environ:
        os.environ[key] = val
