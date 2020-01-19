# FETcher

[GitHub](https://github.com/Parcly-Taxel/FETcher)

This repository contains a script, `fetch.py`, performing **F**il**E T**ransfer for the purposes of [CATcher](https://github.com/CATcher-org/CATcher). It takes from the command line

* the location of a CSV file containing student usernames (see `fetcher/data.csv` for how it should be structured)
* a destination repository in the form `username/reponame`

At the script's beginning, strings must also be set for the name and email address associated with the commit and the username and password that will be used for pushing. The script then clones the students' repositories, transfers them to a central folder in the destination repository called `files`, commits and pushes.

Example times for transferring the CS2103/T AY1920S1 cohort (332 students):
```
real    15m2.305s
user    2m7.910s
sys     0m10.769s
```
[Fet](https://en.wikipedia.org/wiki/Fet) is also the name of a Norwegian municipality, quite close to Akershus Fortress.
