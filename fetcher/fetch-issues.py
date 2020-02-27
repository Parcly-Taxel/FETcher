#!/usr/bin/env python3.7
import json
import argparse
import requests

issues_query = """
query($after: String, $owner: String!, $name: String!) {
repository(owner: $owner, name: $name) {
issues(first: 100, after: $after) {
nodes {title body labels(first: 10) {nodes {name color}}}
pageInfo {endCursor hasNextPage}}}}
"""

# Adapted from https://gist.github.com/gbaman/b3137e18c739e0cf98539bf4ec4366ad
def query_graphql(query, variables, token):
    """Query GitHub's GraphQL API with the given query and variables.
    The response JSON always has a "data" key; its value is returned
    as a dictionary."""
    header = {"Authorization": f"token {token}"}
    r = requests.post("https://api.github.com/graphql",
            json={"query": query, "variables": variables}, headers=header)
    r.raise_for_status()
    return r.json()["data"]

def query_rest(method, endpoint, params, token, extra_headers={}):
    """Query GitHub's REST API with the given method, endpoint
    and parameters. Return the response JSON as a dictionary."""
    header = {"Authorization": f"token {token}"}
    header.update(extra_headers)
    r = requests.request(method, "https://api.github.com" + endpoint,
            json=params, headers=header)
    if not r.ok:
        print(r.headers)
        print(r.json())
        0 / 0
    return r.json()

def get_issue_data(path, token):
    """If path is a JSON file (ending in .json), read that file. Otherwise,
    path must be a repository in owner/name format; save to issues.json
    as backup afterwards.
    In either case, return (1) a list of 3-tuples (title, body, label names)
    for each issue in the repository, and (2) a mapping from names to colours
    for the labels. GraphQL is used in this stage, and only this stage."""
    if path.endswith(".json"):
        with open(path, 'r') as f:
            return json.load(f)
    owner, name = path.split("/")
    variables = {"owner": owner, "name": name}
    issues, label_map, next_page = [], {}, True
    while next_page:
        r = query_graphql(issues_query, variables, token)["repository"]
        for issue in r["issues"]["nodes"]:
            labels = issue["labels"]["nodes"]
            label_map.update({x["name"]: x["color"] for x in labels})
            issue["labels"] = [x["name"] for x in labels]
            issues.append({"issue": issue})
        print(f"{len(issues)} issues received")
        page_info = r["issues"]["pageInfo"]
        next_page = page_info["hasNextPage"]
        variables["after"] = page_info["endCursor"]
    result = (issues, label_map)
    with open("issues.json", 'w') as f:
        json.dump(result, f, indent="  ")
    return result

def create_labels(owner_name, labels, token):
    """Create all given labels not existing in the given repository
    (owner/name format). Return None."""
    r = query_rest("GET", f"/repos/{owner_name}/labels?per_page=100", {}, token)
    existing = {x["name"]: x["color"] for x in r}
    for (name, colour) in labels.items():
        if name in existing:
            continue
        query_rest("POST", f"/repos/{owner_name}/labels",
                {"name": name, "color": colour}, token)

def create_issues(owner_name, issues, token):
    """Create the given issues in the given repository (owner/name format).
    Return None."""
    N = len(issues)
    for (n, issue) in enumerate(issues, 1):
        query_rest("POST", f"/repos/{owner_name}/import/issues", issue, token,
                {"Accept": "application/vnd.github.golden-comet-preview+json"})
        if n % 10 == 0:
            print(f"{n}/{N} issues imported")
        with open("remaining.json", 'w') as f:
            json.dump((issues[n:], {}), f, indent="  ")
    print("all done")

def read_access_token(file):
    """file contains a GitHub access token with repo permissions on
    its last line. Return this token."""
    with open(file, 'r') as f:
        return f.read().splitlines()[-1]

def main():
    """Fetch all issues from the given repository, saving their
    title, body and labels as a JSON file."""
    parser = argparse.ArgumentParser(description="Fetch all issues "
            "from the given repository, writing title, body and labels "
            "to issues.json.")
    parser.add_argument("source", help="source repository in the form "
            "owner/name (e.g. nus-cs2103-AY1920S1/ped-dev-response), "
            "or path to JSON file (e.g. issues.json)")
    parser.add_argument("destination", help="destination repository, "
            "in the form owner/name")
    parser.add_argument("credentials", help="credentials file, "
            "same format as for fetch.py")
    args = parser.parse_args()
    TOKEN = read_access_token(args.credentials)
    issues, labels = get_issue_data(args.source, TOKEN)
    create_labels(args.destination, labels, TOKEN)
    create_issues(args.destination, issues, TOKEN)

if __name__ == "__main__":
    main()
