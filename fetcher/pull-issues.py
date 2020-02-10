#!/usr/bin/env python3.7
from github import Github

g = Github()
repo = g.get_repo("nus-cs2103-AY1920S1/ped-dev-response")
issues = repo.get_issues()
for issue in issues:
    print(issue.title)
