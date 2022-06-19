from setuptools import setup

setup(
    name="eso-banana",
    version="0.0.2",
    scripts=["banana.py"],
    entry_points={
        "console_scripts": [
            "eso-banana-script = banana:periodical_script",
            "eso-ttc = banana:ttc",
        ],
    },
    install_requires=["packaging", "requests"],
    python_requires=">3",
)
