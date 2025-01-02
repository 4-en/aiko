# setup.py

from setuptools import setup, find_packages



deps = [
]

setup(
    name="Aiko2",
    version="0.2.0",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=deps,
    entry_points={
        'console_scripts': [
            'aiko = aiko.main:main'
        ]
    },
)


