import setuptools

with open('README.md', 'r') as fh:
    long_desc = fh.read()


with open('LICENSE', 'r') as fh:
    license = fh.read()

setuptools.setup(
    name                          = 'Tagsnag',
    version                       = '0.9.0',
    author                        = 'Thomas Johannesmeyer',
    author_email                  = 'opensource@geeky.gent',
    description                   = 'Search files over multiple Git repos, and extract a certain version',
    long_description              = long_desc,
    long_description_content_type = 'text/markdown',
    license                       = license,
    url                           = 'https://github.com/beulenyoshi/tagsnag',
    packages                      = setuptools.find_packages(exclude = ('tests', 'docs')),
    entry_points                  = {
                                        'console_scripts': ['tagsnag=tagsnag.__main__:main'],
                                    },
    install_requires              = [
                                        'gitpython',
                                    ],

    classifiers                   = [
                                        'Programming Language :: Python :: 3',
                                        'License :: OSI Approved :: MIT License',
                                        'Operating System :: OS Independent',
                                    ]
)
