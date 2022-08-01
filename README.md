![OCDC Logo](/logo.png)

<h2 align="center">Obsessive-Compulsive Development Changelogs</h2>

`ocdc` is a changelog formatter for "people", neat freaks, and sloppy typists.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
with some slight modifications:

- Lines are wrapped at 90 characters.
- Version sections are separated by two blank lines to aid visual scanning.
- Square brackets are not used in titles. Changelogs aren't programming
  languages, so why throw in weird symbols like that?


## Installation

```console
$ pip install ocdc
```


## Usage

To format `CHANGELOG.md` in the current directory, run `ocdc` without arguments.
You can also pass a custom path.

```console
$ ocdc [--path CHANGELOG.md]
```

To check `CHANGELOG.md` without modifying the file, use `--check`.

```console
$ ocdc --check [--path CHANGELOG.md]
```

To create a new `CHANGELOG.md`, use the `new` subcommand.

```console
$ ocdc new [--force]
```

For a description of all options, use `--help`.

```console
$ ocdc --help
```


## Configuration

Configuration is for the weak-willed. There shall be only one true format.


## Disclaimer

This thing is new, and it might eat your changelog! Back up your files (in git)
before trying `ocdc`.
