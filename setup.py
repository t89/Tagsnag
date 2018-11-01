import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name                          = "Tagsnatch",
    version                       = "0.0.0",
    author                        = "Thomas Johannesmeyer",
    author_email                  = "opensource@geeky.gent",
    description                   = "Search files over multiple Git repos, and extract a certain version",
    long_description              = long_description,
    long_description_content_type = "text/markdown",
    url                           = "https://github.com/beulenyoshi/tagsnag",
    packages                      = setuptools.find_packages(),
    classifiers                   = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
