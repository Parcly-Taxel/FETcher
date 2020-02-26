# FETcher

[GitHub](https://github.com/Parcly-Taxel/FETcher)

This repository contains two Python scripts. The first, `fetch.py`, performs **F**il**E T**ransfer for the purposes of [CATcher](https://github.com/CATcher-org/CATcher). It takes from the command line

* either the location of a CSV file containing student usernames (see `fetcher/data.csv` for how it should be structured), or a regular file containing one username per line to transfer
* a destination repository in the form `owner/name`
* a credentials file, containing four lines of author name, email address, GitHub username and access token, e.g.
```
Derpy Hooves
derpy@equestria.net
muffinsmuffins
4f17daf987b3028dd4367f8bef6ec39e929203a8
```

The script then clones the students' repositories, transfers their files to a central folder in the destination repository called `files`, commits and pushes.

An interrupted transfer process can be resumed by passing `remaining` instead of the CSV file as the first argument to `fetch.py`. The file `remaining` is automatically updated with a list of usernames still to process.

Example times for transferring the CS2103/T AY1920S1 cohort (332 students):
```
real    15m2.305s
user    2m7.910s
sys     0m10.769s
```

The second script, `pull-issues.py`, takes from the command line

* a source and destination repository, both in the form `owner/name`
* a credentials file as in `fetch.py`

It then

* downloads the _title_, _body_ and _labels_ of all issues in the source repository using [GitHub's GraphQL API](https://developer.github.com/v4) and saves them to `issues.json` as a backup
* creates issues with the same data in the destination repository

----

[Fet](https://en.wikipedia.org/wiki/Fet) is also the name of a Norwegian municipality, quite close to Akershus Fortress.
