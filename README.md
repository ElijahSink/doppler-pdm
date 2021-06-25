# doppler-pdm

[![pypi](https://img.shields.io/pypi/v/doppler-pdm?logo=python&logoColor=%23cccccc)](https://pypi.org/project/doppler-pdm/)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)

A plugin for PDM that enables first-class [Doppler](https://www.doppler.com/) envvar support.

## Installation

### via pipx

`pipx inject pdm doppler-pdm`

### via brew

`$(brew --prefix pdm)/libexec/bin/python -m pip install pdm-publish`

### via pip

`pip install --user doppler-pdm`

## Usage

doppler-pdm enables pdm to load environment variables from Doppler similarly to how they are loaded from .env files.

This requires that the doppler CLI be installed, logged in, and that the current directory is configured with a project and environment. Those are typically set by running `doppler setup`.

Suppose that you have some secret stored in Doppler: `YOUR_SECRET=mmmm_tasty`

This behavior can be configured in the following three different ways, _with increasing priority_:

1. Via global env settings with the `_` key

   ```toml
   [tool.pdm.scripts]
   _.doppler = true # default false
   ```

2. Via individual script definitions (overrides 1)

   ```toml
   [tool.pdm.scripts]
   with = { cmd="echo $YOUR_SECRET", doppler=true } # default false
   without = { cmd="echo $YOUR_SECRET" }
   ```

3. Via the command line (overrides 1 and 2)

   ```
   $ pdm run --doppler without
   mmmm_tasty

   $ pdm run --no-doppler with


   ```

Running other commands that are not defined in the pyproject.toml is also supported.

```
$ pdm run echo \$YOUR_SECRET


$ pdm run --doppler echo \$YOUR_SECRET
mmmm_tasty
```

Other commands are still governed by the global `_.doppler` setting
