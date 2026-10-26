

## Overview

`mousike` is a python library for reading ancient Greek musical notation in Zach Sowerby's notational scheme, and translating this notation to MIDI files in a variety of ancient tuning systems.

## Functionality

The python library should be packaged for publication on pypi. API docs should be automatically built.


## Architecture & Directory Structure

- `quarto`, `docs`, `README.md` and `releases.md` are all user-readable content owned by me; Claude should not touch them
- `notes` is for documentation and notes that Claude writes, includes session summaries so I can reliably pick up working with Claude from different machines
- `src` is for source code


## Testing Guidelines

- Write unit tests for utility functions and integration/component tests for critical UI flows.
- Run relevant tests before proposing significant refactors.