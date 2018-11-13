import setuptools

with open('README.md', 'r') as fh:
    long_description = fh.read()


with open('LICENSE', 'r') as fh:
    license = fh.read()

setuptools.setup(
    name                          = 'Tagsnatch',
    version                       = '0.6.2',
    author                        = 'Thomas Johannesmeyer',
    author_email                  = 'opensource@geeky.gent',
    description                   = 'Search files over multiple Git repos, and extract a certain version',
    long_description              = long_description,
    license                       = license,
    long_description_content_type = 'text/markdown',
    url                           = 'https://github.com/beulenyoshi/tagsnag',
    packages                      = setuptools.find_packages(exclude = ('tests', 'docs')),
    classifiers                   = [
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ]
)
