#!/usr/bin/env python3

import os
import io
from setuptools import find_packages, setup

VERSION = "0.2.0"

here = os.path.abspath(os.path.dirname(__file__))
with io.open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

setup(
    name="datatops",
    version=VERSION,
    author="Jordan Matelsky",
    author_email="opensource@matelsky.com",
    description=(
        "Datatops is a super-simple zero-auth zero-setup data storage and retrieval tool for small, low-traffic projects."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="Apache 2.0",
    keywords=["database", "serverless"],
    url="https://github.com/j6k4m8/datatops/tarball/" + VERSION,
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    classifiers=[],
    install_requires=["requests", "flask"],
    extras_require={
        "aws": ["boto3"],
    },
)
