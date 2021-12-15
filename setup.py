from setuptools import setup

setup(
    name="eso-banana",
    version="0.0.1",
    packages=["banana"],
    entry_points={
        "console_scripts": ["eso-banana-script = banana:scripts.periodical_script"],
    },
    python_requires=">3",
    install_requires=[
        "packaging",
        "PyYAML",
        "requests",
    ],
)
