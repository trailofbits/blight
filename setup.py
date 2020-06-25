#!/usr/bin/env python3

from setuptools import setup

version = {}
with open("./src/canker/version.py") as f:
    exec(f.read(), version)

with open("./README.md") as f:
    long_description = f.read()

setup(
    name="canker",
    version=version["__version__"],
    license="MIT",
    author="William Woodruff",
    author_email="william@trailofbits.com",
    description="A catch-all compile-tool wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trailofbits/canker",
    packages=["canker"],
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "canker-env = canker.cli:env",
            "canker-cc = canker.cli:tool",
            "canker-c++ = canker.cli:tool",
            "canker-cpp = canker.cli:tool",
            "canker-ld = canker.cli:tool",
            "canker-as = canker.cli:tool",
        ],
    },
    platforms="any",
    python_requires=">=3.6",
    install_requires=[
        "click ~= 7.1",
    ],
    extras_require={
        "dev": [
            "flake8",
            "black",
            "isort[pyproject]",
            "pytest",
            "pytest-cov",
            "twine",
        ]
    }
)
