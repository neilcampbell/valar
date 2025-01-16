# Contributing

You are welcome to help is improve the Valar Daemon.
The below commands can assist you in building the package and docs with the default tools.

You can step in contact with us on one of the official communication channels, found in [the project's README.md](../../README.md) or on [stake.valar.solutions](http://stake.valar.solutions)

## Build

### Build the package

Building the package is possible using `poetry build`.

The build configuration is in `pyproject.toml`.

### Build the docs

To build the docs run `pdoc --docformat numpy --footer-text "Valar Daemon v<v.v.v>" src/valar_daemon --output-dir dist-docs`.

The results are stored in the directory `dist-docs`, where the main file for opening the docs locally is `./dist-docs/index.html`.
