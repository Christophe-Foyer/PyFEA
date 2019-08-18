import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="python-fea",
    version="0.0.1",
    author="Christophe Foyer",
    author_email="christophe@cfoyer.com",
    description="A 3D transient FEA package in python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Christophe-Foyer/pyFEA",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)