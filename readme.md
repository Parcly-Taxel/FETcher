# FETcher

[GitHub](https://github.com/Parcly-Taxel/fetcher)

This repository contains a script, `fetch.py`, to transfer files for the purposes of [CATcher](https://github.com/CATcher-org/CATcher). It takes from the command line

* the location of a CSV file containing student usernames (see `fetcher/data.csv` for how it should be structured)
* a destination repository in the form `username/reponame`

At the script's beginning, strings must also be set for the name and email address associated with the commit and the username and password that will be used for pushing.

The script then clones the students' repositories, transfers them to a central folder in the destination repository called `files`, commits and pushes.

Example times for transferring the CS2103/T AY1920S1 cohort:
```
real    15m2.305s
user    2m7.910s
sys     0m10.769s
```
