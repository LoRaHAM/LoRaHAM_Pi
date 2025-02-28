import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyLoRa",
    version="0.3.1",
    author="Rui Silva",
    author_email="ruisilva.real@sapo.pt",
    description="(LoRa communication 868MHz VERSION) This is a python interface to the Semtech SX1276/7/8/9 long range, low power transceiver family.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/rpsreal/pySX127x",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "Natural Language :: Portuguese",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ),
)
