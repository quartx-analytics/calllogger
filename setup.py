#!/usr/bin/env python
from setuptools import setup as finalize, find_packages
from codecs import open

setup = dict(
    version="0.1.1",
    name="call-logger",
    description="Call logger component for the phone system monitoring frontend.",
    keywords="siemens hipath phone call calls",
    author="William Forde,Michael Forde",
    author_email="willforde@gmail.com",
    url="https://github.com/callmonitoring/call_logger",
    license="BSD License",  # example license
    platforms="OS Independent",
    python_requires=">=3.6",
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    zip_safe=False,
    project_urls={
        'Documentation': 'https://callmonitoring.github.io/call_monitoring/',
        'Source': 'https://github.com/callmonitoring/call_logger',
        'Tracker': 'https://github.com/callmonitoring/call_monitoring/issues',
    },
)


# Readme
# ######

setup["long_description_content_type"] = "text/markdown"
with open("README.md", "r", encoding="utf-8") as stream:
    setup["long_description"] = stream.read()


# Dependencies
# ############

setup["install_requires"] = [
    "phonenumbers",
    "pyserial",
    "requests",
    "appdirs",
    "django"
]


# Classifiers
# ###########
# Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers

classifiers = setup.setdefault("classifiers", [])
classifiers.extend([
    "Natural Language :: English",
    "Intended Audience :: System Administrators",
    "Development Status :: 5 - Production/Stable",
    "Environment :: No Input/Output (Daemon)",
    "Framework :: Django",
    "Framework :: Django :: 2.0"
])

if setup.get("platforms") == "OS Independent":
    classifiers.append("Operating System :: OS Independent")

if setup.get("license") == "BSD License":
    classifiers.append("License :: OSI Approved :: BSD License")

classifiers.append("Programming Language :: Python :: 3")
for py_versions in ["Only", 3.6, 3.7]:
    classifiers.append("Programming Language :: Python :: 3 :: {}".format(py_versions))


# Finalize
# ########

finalize(**setup)
