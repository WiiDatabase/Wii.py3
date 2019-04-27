from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="Wii.py3",
    version="0.0.2",
    author="WiiDatabase.de",
    description="Wii Python library for Python 3.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/WiiDatabase/Wii.py3",
    packages=["Wii"],
    install_requires=["pycryptodome"],
    license="GNU GPL v3",
    python_requires=">=3.4",
    classifiers=[
        "Development Status :: 3 - Alpha",

        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",

        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",

        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],
)
