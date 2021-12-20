#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

def read_requirements(path: str):
    with open(path) as f:
        return f.read().splitlines()

with open("README.md") as readme_file:
    readme = readme_file.read()

with open("HISTORY.md") as history_file:
    history = history_file.read()

install_requirements = read_requirements("requirements.txt")

setup(
    author="Robnet Kerns",
    author_email="robnet@jataware.com",
    python_requires=">=3.5",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="A command-line interface for black box model execution.",
    entry_points={
        "console_scripts": [
            "dojo=dojocli.cli:cli",
        ],
    },
    #setup_requires=["numpy>=1.20.1"],  # This is not working as expected
    install_requires=install_requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords="dojo-cli",
    name="dojo-cli",
    package_data={'dojocli' : ['data/*']},
    packages=find_packages(include=["dojocli", "dojocli.*"]),
    test_suite="tests",
    url="https://github.com/dojo-modeling/dojo-cli",
    version='0.1.2',
    zip_safe=False,
)
