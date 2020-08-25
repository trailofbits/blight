#!/usr/bin/env python3

from setuptools import find_packages, setup

version = {}
with open("./src/blight/version.py") as f:
    exec(f.read(), version)

with open("./README.md") as f:
    long_description = f.read()

setup(
    name="blight",
    version=version["__version__"],
    license="Apache-2.0",
    author="William Woodruff",
    author_email="william@trailofbits.com",
    description="A catch-all compile-tool wrapper",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/trailofbits/blight",
    project_urls={"Documentation": "https://trailofbits.github.io/blight/"},
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        "console_scripts": [
            "blight-env = blight.cli:env",
            "blight-cc = blight.cli:tool",
            "blight-c++ = blight.cli:tool",
            "blight-cpp = blight.cli:tool",
            "blight-ld = blight.cli:tool",
            "blight-as = blight.cli:tool",
        ]
    },
    platforms="any",
    python_requires=">=3.7",
    install_requires=["click ~= 7.1", "typing_extensions"],
    extras_require={
        "dev": [
            "flake8",
            "black",
            "isort",
            "pytest",
            "pytest-cov",
            "coverage[toml]",
            "twine",
            "pdoc3",
            "mypy",
        ]
    },
)
