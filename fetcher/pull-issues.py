#!/usr/bin/env python3.7
import json
import argparse
import requests

# Issues are created in groups of this size
BATCH_SIZE = 10

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

labels_query = """
query($owner:String!, $name:String!) {
  repository(owner: $owner, name: $name) {
    id
    labels(first: 100) {
      nodes {
        id
        name
        color
      }
    }
  }
}
"""

def repository_variables(owner_name):
    """Split the given repository identifier into owner and name parts.
    Return a dictionary suitable for use with GraphQL."""
    owner, name = owner_name.split("/")
    return {"owner": owner, "name": name}

# Adapted from https://gist.github.com/gbaman/b3137e18c739e0cf98539bf4ec4366ad
def query_github_graphql(query, variables, access_token, extra_headers={}):
    """Query the GitHub GraphQL API with the given access token,
    query and variables. The response JSON is returned as a dictionary."""
    header = {"Authorization": f"token {access_token}"}
    header.update(extra_headers)
    r = requests.post("https://api.github.com/graphql",
            json={"query": query, "variables": variables}, headers=header)
    r.raise_for_status()
    return r.json()

def get_labels(variables, access_token):
    """Query the labels of the repository corresponding to the given
    GraphQL variables (owner and name). Return a dictionary mapping
    names to colours, one mapping names to IDs and the repository's ID.
    Assume there are not more than 100 labels."""
    res = query_github_graphql(labels_query, variables, access_token)
    repository_id = res["data"]["repository"]["id"]
    res = res["data"]["repository"]["labels"]["nodes"]
    return ({x["name"]: x["color"] for x in res},
            {x["name"]: x["id"] for x in res}, repository_id)

def get_issue_data(path, access_token):
    """If path is a JSON file (ending in .json), read that file. Otherwise,
    path must be a repository name in owner/name format. Return (A, B) where
    A is a list of 3-tuples, each tuple bearing (title, body, label names)
    for each issue in the repository, and B is the output of get_labels()[0].
    If path is a repository, this data is also saved to issues.json as backup."""
    if path.endswith(".json"):
        with open(path, 'r') as f:
            return json.load(f)

    variables = repository_variables(path)
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
    labels = get_labels(variables, access_token)[0]
    result = [issues, labels]
    with open("issues.json", 'w') as f:
        json.dump(result, f, indent="  ")
    return result

def labels_block(repository_id, labels):
    """Generate the mutation block that will add all given labels
    (a dictionary mapping names to colours) to the repository
    with the given ID."""
    mutations = []
    for (n, (name, colour)) in enumerate(labels.items()):
        mut = (f'l{n}: createLabel(input: {{repositoryId: "{repository_id}", '
                f'name: "{name}", color: "{colour}"}})'
                f'{{label{{id name}}}}')
        mutations.append(mut)
    return "mutation {\n" + "\n".join(mutations) + "\n}"

def create_labels(owner_name, new_labels, access_token):
    """Create all given labels not existing in the given repository.
    Return a dictionary mapping labels to IDs in the given repository
    and said repository's ID."""
    variables = repository_variables(owner_name)
    _, labels, destination_id = get_labels(variables, access_token)
    new_labels = {k: v for (k, v) in new_labels.items() if k not in labels}
    if not new_labels:
        return (labels, destination_id)
    mutations = labels_block(destination_id, new_labels)
    res = query_github_graphql(mutations, {}, access_token,
            {"Accept": "application/vnd.github.bane-preview+json"})
    new_pairs = {label["label"]["name"]: label["label"]["id"]
            for label in res["data"].values()}
    labels.update(new_pairs)
    return (labels, destination_id)

def issues_block(repository_id, issues, labels):
    """Generate the mutation block that will add all given issues
    to the given repository. num is an index, which should be unique.
    labels is a mapping from label names to IDs."""
    mutations = []
    for (n, issue) in enumerate(issues):
        title, body, label_list = issue
        title = json.dumps(title)
        body = json.dumps(body)
        label_list = json.dumps([labels[l] for l in label_list])
        mut = (f'i{n}: createIssue(input: {{repositoryId: "{repository_id}", '
                f'title: {title}, body: {body}, '
                f'labelIds: {label_list}}}){{issue{{number}}}}')
        mutations.append(mut)
    return "mutation {\n" + "\n".join(mutations) + "\n}"

def create_issues(repository_id, issues, labels, access_token):
    """Create the given issues (output of get_issue_data()) in the
    repository with the given ID. labels is a mapping from labels to IDs.
    Return the numbers of the issues thus created."""
    N = len(issues)
    out = []
    for i in range(0, N, BATCH_SIZE):
        lim = min(i+BATCH_SIZE, N)
        batch = issues[i:lim]
        mutations = issues_block(repository_id, batch, labels)
        res = query_github_graphql(mutations, {}, access_token)
        print(res)
        with open("remaining.json", 'w') as f:
            json.dump([issues[lim:], labels], f, indent="  ")
        print(f"{lim}/{N}")
        out.extend(issue["issue"]["number"] for issue in res["data"].values())
    return out

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
    labels, destination_id = create_labels(args.destination, labels, TOKEN)
    res = create_issues(destination_id, issues, labels, TOKEN)
    print(res)

if __name__ == "__main__":
    main()
