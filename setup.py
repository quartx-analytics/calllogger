#!/usr/bin/env python
from setuptools import setup as finalize, find_packages
from codecs import open
import os

setup = dict(
    version="0.1.1",
    name="quartx-call-logger",
    description="Call logger component for the QuartX phone system monitoring frontend.",
    keywords="siemens hipath phone call calls",
    author="William Forde,Michael Forde",
    author_email="willforde@gmail.com",
    url="https://quartx.ie/",
    license="MIT License",
    platforms="OS Independent",
    python_requires=">=3.6",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    project_urls={
        'Documentation': '',
        'Source': 'https://github.com/quartx-software/quartx-call-logger',
        'Tracker': 'https://github.com/quartx-software/quartx-call-logger/issues',
    },
)


# Readme
# ######

setup["long_description_content_type"] = "text/markdown"
if os.path.exists("README.md"):
    with open("README.md", "r", encoding="utf-8") as stream:
        setup["long_description"] = stream.read()


# Dependencies
# ############

#setup["install_requires"] = [line.strip() for line in open("requirements.txt")]
#setup["test_requires"] = [line.strip() for line in open("requirements-dev.txt")]
setup["install_requires"] = [
    "pytest",
    "pytest-cov",
    "requests-mock",
    "pyserial",
    "requests",
    "appdirs",
    "systemd-python",
    "pyyaml",
]


# Classifiers
# ###########
# Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers

classifiers = setup.setdefault("classifiers", [])
classifiers.extend([
    "License :: OSI Approved :: MIT License",
    "Natural Language :: English",
    "Intended Audience :: System Administrators",
    "Development Status :: 5 - Production/Stable",
    "Environment :: No Input/Output (Daemon)"
])

if setup.get("platforms") == "OS Independent":
    classifiers.append("Operating System :: OS Independent")

classifiers.append("Programming Language :: Python :: 3")
for py_versions in ["Only", 3.6, 3.7]:
    classifiers.append("Programming Language :: Python :: 3 :: {}".format(py_versions))


# Finalize
# ########

finalize(**setup)
