# FETcher

[GitHub](https://github.com/Parcly-Taxel/fetcher)

This repository contains a script, `fetch.py`, to transfer files for the purposes of [CATcher](https://github.com/CATcher-org/CATcher). It takes from the command line

* the location of a CSV file containing student usernames (see `fetcher/data.csv` for how it should be structured)
* a destination repository in the form `username/reponame`

The script then clones the students' repositories, transfers them to a central folder in the destination repository called `files`, commits and pushes.
