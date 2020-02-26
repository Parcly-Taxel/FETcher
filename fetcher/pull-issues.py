#!/usr/bin/env python3.7
import json
import argparse
import requests

issues_query = """
query($after:String, $owner:String!, $name:String!) {
  repository(owner: $owner, name: $name) {
    issues(first: 100, after: $after) {
      totalCount
      nodes {
        title
        body
        labels(first: 50) {
          nodes {
            name
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""

# Adapted from https://gist.github.com/gbaman/b3137e18c739e0cf98539bf4ec4366ad
def query_github_graphql(query, variables, access_token):
    """Query the GitHub GraphQL API with the given access token,
    query and variables. The response JSON is returned as a dictionary."""
    header = {"Authorization": f"token {access_token}"}
    r = requests.post("https://api.github.com/graphql",
            json={"query": query, "variables": variables}, headers=header)
    r.raise_for_status()
    return r.json()

def get_issues(owner_name, access_token):
    """Retrieve the title, body and labels of all issues in
    the repository owner/name. Return a list of 3-tuples,
    each tuple bearing (title, body, labels)."""
    owner, name = owner_name.split("/")
    variables = {"owner": owner, "name": name}
    issues = []
    while True:
        res = query_github_graphql(issues_query, variables, access_token)
        res = res["data"]["repository"]
        print(f"{len(issues)}/{res['issues']['totalCount']}")
        for issue in res["issues"]["nodes"]:
            title = issue["title"]
            body = issue["body"]
            labels = [x["name"] for x in issue["labels"]["nodes"]]
            issues.append((title, body, labels))
        page_info = res["issues"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        variables["after"] = page_info["endCursor"]
    return issues

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
    parser.add_argument("source", help="source repository, "
            "in the form owner/name (e.g. nus-cs2103-AY1920S1/ped-dev-response)")
    parser.add_argument("credentials", help="credentials file, "
            "same format as for fetch.py")
    args = parser.parse_args()
    TOKEN = read_access_token(args.credentials)
    issues = get_issues(args.source, TOKEN)
    with open("issues.json", 'w') as f:
        json.dump(issues, f, indent="  ")

if __name__ == "__main__":
    main()
