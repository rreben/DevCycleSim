# type: ignore
from setuptools import setup, find_packages

setup(
    name="devcyclesim",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'numpy',
    ],
    entry_points={
        'console_scripts': [
            'devcyclesim=devcyclesim.src.cli:cli',
        ],
    },
)
