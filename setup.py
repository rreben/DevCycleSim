# type: ignore
from setuptools import setup, find_packages

setup(
    name="devcyclesim",
    version="0.1.2",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'numpy',
        'pandas',
        'matplotlib',
    ],
    entry_points={
        'console_scripts': [
            'devcyclesim=devcyclesim.src.cli:run',
        ],
    },
)
