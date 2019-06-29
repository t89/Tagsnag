![Tagsnag](./docs/Icon/Multi.png)

# Tagsnag

The idea behind Tagsnag is to provide a quick & easy to use cli-tool to extract data for comparison from a *similar version* over *multiple* repositories. It was written with educational use in mind: Imagine `n` groups of students handing in assignments via `n` Git repositories. The assignments are tagged rather similary and follow the same structure roughly.


## Installation

### Install using pip:

```bash
$ pip install Tagsnag
```


### Manual Installation

Tagsnag uses `Python 3.7` and requires `Gitpython` to be installed. You can install it using the provided `Makefile`:

```bash
$ make init
```

Or manually using `pip`:

```bash
$ pip install gitpython
```


## Run

To run `tagsnag` over all repositories in a directory enter the directory via shell. The whole set of commands can be found by calling `--help`.

## Overview

| Flag              | Description                                                                                          |
| :---              | :---                                                                                                 |
| `-l, --log`       | Create a logfile.                                                                                    |
| `-p, --prune`     | [Read Git manual.](https://git-scm.com/docs/git-prune) May come in handy if tags are replaced a lot. |
| `-s, --autostash` | Instead of skipping the untidy repository, stash all changes.                                        |
| `-u, --update`    | Run `git checkout master && git pull origin master` on all repositories.                             |
| `-v, --verbose`   | Additional logging.                                                                                  |


| Modes                  | Necessary Arguments                                        |
| :---                   | :---                                                       |
| **Extract File**       | `tagsnag --tag=<tag> --filename=<name> --extension=<type>` |
| **Extract Dir**        | `tagsnag --tag=<tag> --directory=<name>`                   |
| **Extract via XML**    | *(Deprecated)* `tagsnag --xml=<path>`                      |
| `--destination=<name>` | *Optional:* Name created destination folder                |


## Updating repositories

Run `git checkout master && git pull origin master` on all repositories:

```bash
$ tagsnag --update
```

## File extraction

```bash
$ tagsnag --tag=<tag>            \
--filename=<filename>            \
--extension=<filetype>           \
--destination=<destination_path>
```

The following sample will fuzzy search for a tag containing `1.0`, check it out and search for a file of type `.md` containing the string `readme` in its name. This file will then be copied into the destination folder and be renamed to `<repository_name>.md`:

```bash
$ tagsnag                   \
--tag=1.0                   \
--filename=readme           \
--extension=md              \
--destination=./ReadmeFiles
```

## Directory extraction

Instead of a filename, you can provide a directory name to extract. Tagsnag will copy the first directory it finds matching the name starting from `root`.

```bash
$ tagsnag --tag=<tag>              \
--directory=<directory_name>     \
--destination=<destination_path>
```


### Run with XML file

- For more configurability you can put an `xml` file into the folder containing the repos and run it:

```bash
$ tagsnag --xml=<path/of/xml_file>
```


## Authors

* **Thomas Johannesmeyer** - [www.geeky.gent](http://geeky.gent)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details

## Support

The framework and code are provided as-is, but if you need help or have suggestions, you can contact me anytime at [opensource@geeky.gent](mailto:opensource@geeky.gent?subject=Tagsnag).


## I'd like to hear from you

If you have got any suggestions, please feel free to share them with me. :)
