#!/usr/bin/env python3.7
import os
import csv
import shutil
import tempfile
import argparse
import multiprocessing

import pygit2

def clone_destination(owner_name, key):
    """If the destination repository given by owner/name does not exist,
    clone it. key is a RemoteCallbacks object for authentication to GitHub.
    Return a Repository object in any case."""
    name = owner_name.partition("/")[2]
    if os.path.exists(name):
        return pygit2.Repository(name)
    git_path = f"https://github.com/{owner_name}.git"
    return pygit2.clone_repository(git_path, name, callbacks=key)

def make_files_folder(repository):
    """Return a path to a folder called files in the given
    Repository object, making it if needed."""
    files_path = os.path.join(repository.workdir, "files")
    os.makedirs(files_path, exist_ok=True)
    return files_path

def clone_files(pair):
    """pair = (name, parent). Clone the named student's PE repository
    into parent and return (name, path), where path is name/files or
    None if the repository does not exist.
    parent/name should not already exist."""
    name, parent = pair
    try:
        git_path = f"git://github.com/{name}/pe.git"
        repo_path = os.path.join(parent, name)
        pygit2.clone_repository(git_path, repo_path)
    except pygit2.GitError:
        return (name, None)
    files_path = os.path.join(repo_path, "files")
    return (name, files_path if os.path.isdir(files_path) else None)

def transfer_files(src, dst):
    """Transfer all files from src into dst, returning any clashing
    filenames (not transferred after the first) as a list."""
    clashes = []
    files_in_dst = os.listdir(dst)
    for filename in os.listdir(src):
        full_filename = os.path.join(src, filename)
        if filename in files_in_dst:
            clashes.append(full_filename)
        else:
            shutil.copy(full_filename, dst)
    return clashes

def get_user_and_filename(path):
    """Extract the user and filename from the full paths returned
    from transfer_files(), which indicate clashing filenames."""
    segments = os.path.normpath(path).split(os.sep)
    return segments[-3] + "/" + segments[-1]

def dump_remaining_usernames(names):
    """Dump names yet to be processed into a backup file."""
    with open("remaining", 'w') as f:
        for name in names:
            print(name, file=f)

def collate_files(names, endpoint):
    """Given a sequence of GitHub usernames of students, clone their
    PE repositories and copy files into endpoint. Return a list of
    duplicate filenames found in the form username/filename."""
    clashes = []
    N = len(names)
    left_names = set(names)
    with tempfile.TemporaryDirectory() as tempdir, \
            multiprocessing.Pool() as pool:
        pairs = [(name, tempdir) for name in names]
        results = pool.imap(clone_files, pairs)
        for (n, (name, name_path)) in enumerate(results, 1):
            print(f"{n}/{N} {name}")
            left_names.remove(name)
            dump_remaining_usernames(left_names)
            if name_path is None:
                continue
            clashes += transfer_files(name_path, endpoint)
    return [get_user_and_filename(p) for p in clashes]

def commit_and_push(repository, author, email, message, key):
    """Commit the current working state of repository using the given
    author information and message. Then push changes to the remote
    using key (a RemoteCallbacks object) for authentication."""
    repository.index.add_all()
    repository.index.write()
    signature = pygit2.Signature(author, email)
    tree = repository.index.write_tree()
    repository.create_commit("HEAD", signature, signature, message,
            tree, [repository.head.target])
    remote = repository.remotes["origin"]
    remote.push(["refs/heads/master"], callbacks=key)

def read_student_names(file):
    """If file ends in .csv, read the CSV file where each username should
    reside in the second column and the first column contains "student".
    If not, the file should contain several lines, one username per line.
    Return a list of students thus extracted."""
    with open(file, 'r') as f:
        if not file.endswith(".csv"):
            return f.read().splitlines()
        return [row[1] for row in csv.reader(f) if row[0] == "student"]

def read_credentials(file):
    """file contains four lines: author name, email address,
    GitHub username, access token. Extract these fields
    from said file and return a tuple of them."""
    with open(file, 'r') as f:
        return tuple(f.read().splitlines())

def print_clashes(clashes):
    """Print any clashing filenames that arose out of file transfer."""
    if clashes:
        print("Files not transferred:")
        for clash in clashes:
            print(clash)

def main():
    """Get the CSV file of students' names and the destination
    repository from the command line, then transfer the files.
    Afterwards, commit and push using provided credentials."""
    parser = argparse.ArgumentParser(description="Read a file of "
            "student GitHub usernames, then transfer files in their "
            "PE repositories to a given destination repository.")
    parser.add_argument("students", help="CSV or plaintext list of students")
    parser.add_argument("destination", help="destination repository, "
            "in the form owner/name (e.g. nus-cs2103-AY1920S1/pe)")
    parser.add_argument("credentials", help="credentials file - "
            "four lines of author, email, username, access token")
    args = parser.parse_args()
    students = read_student_names(args.students)

    AUTHOR, EMAIL, USERNAME, TOKEN = read_credentials(args.credentials)
    user_pass = pygit2.UserPass(USERNAME, TOKEN)
    key = pygit2.RemoteCallbacks(credentials=user_pass)

    endpoint = clone_destination(args.destination, key)
    files_path = make_files_folder(endpoint)
    print_clashes(collate_files(students, files_path))
    commit_and_push(endpoint, AUTHOR, EMAIL, "Collect PE files", key)

if __name__ == "__main__":
    main()
