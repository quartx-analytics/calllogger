#!/usr/bin/env python
"""
Classifiers
###########

Classifiers gives the index and pip some additional metadata about your package.
You should always include at least which version(s) of Python the package works on,
which license your package is available under, and which operating systems your
package will work on.

For a complete list of classifiers. see https://pypi.org/classifiers/.


Long Description
################

long_description: is a detailed description of the package. This is shown on the package
detail package on the Python Package Index. In this case, the long description is
loaded from README.md which is a common pattern.

long_description_content_type: tells the index what type of markup is used
for the long description. In this case, it’s Markdown.

long_description_content_type = "text/markdown"  # Markdown
long_description_content_type = "text/x-rst"     # ReStructured Text
long_description_content_type = "text/plain"     # Plan Text


Dependencies
############

The dependency_links option takes the form of a list of URL strings.
For example, the below will cause EasyInstall to search the specified
page for eggs or source distributions, if the package’s dependencies
aren’t already installed

"""
from setuptools import setup as finalize, find_packages
from codecs import open
import os
import re

# The root path of this file
this_directory = os.path.abspath(os.path.dirname(__file__))


setup = dict(
    # Package version in the format: major.minor.micro
    version="0.2.0",

    # Distribution name of this package
    name="quartx-call-logger",

    # Author of the package
    author="William Forde",
    author_email="willforde@quartx.ie",

    # Short, one-sentence summary of the package
    description="Call logger component for the QuartX phone system monitoring frontend.",

    # Homepage of the project
    url="https://quartx.ie/",

    # Package license, see: https://choosealicense.com/
    license="MIT License",

    # The projects packages
    packages=find_packages(exclude=["tests"]),

    # Automatic Script Creation
    entry_points={
        "console_scripts": [
            "call-logger=quartx_call_logger.__main__:main"
        ]
    },

    # True to include files within the MANIFEST.in
    include_package_data=True,

    # False if package uses __file__, True otherwise
    zip_safe=True,

    # Minimum required python version
    python_requires=">=3.6",

    # Keywords used in pip search
    keywords="siemens hipath phone call calls",

    # The platform this package supports
    platforms="OS Independent",

    # Pypi Url
    project_urls={
        'Documentation': 'https://quartx-call-logger.readthedocs.io/en/stable/',
        'Source': 'https://github.com/quartx-software/quartx-call-logger/',
        'Tracker': 'https://github.com/quartx-software/quartx-call-logger/issues/',
    },

    # Classifiers
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Intended Audience :: System Administrators",
        "Development Status :: 5 - Production/Stable",
        "Environment :: No Input/Output (Daemon)",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3 :: 3.6",
        "Programming Language :: Python :: 3 :: 3.7",
        "Topic :: Communications :: Telephony",
        "Topic :: Communications :: Internet Phone",
        "Typing :: Typed",
    ]
)

# Add readme as long description
if os.path.exists(os.path.join(this_directory, "README.rst")):
    setup["long_description_content_type"] = "text/x-rst"
    with open(os.path.join(this_directory, "README.rst"), "r", encoding="utf-8") as stream:
        setup["long_description"] = stream.read()

# Dependencies for normal install
setup["install_requires"] = [
    "pyserial",
    "requests",
    "appdirs",
    "pyyaml"
]

# Dependencies for devlopment install
setup["extras_require"] = {
        "dev": [
            "pytest",
            "pytest-cov",
            "requests-mock"
        ]
    }

# Extract version from package
with open(os.path.join("quartx_call_logger", "__init__.py"), 'r') as opened:
    search_refind = r'__version__ = ["\'](\d+\.\d+\.\d+)["\']'
    verdata = re.search(search_refind, opened.read())
    if verdata:
        setup["version"] = verdata.group(1)
    else:
        raise RuntimeError("Unable to extract version number")

# Actually call setup
finalize(**setup)
