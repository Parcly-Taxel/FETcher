#!/usr/bin/env python3.7
import os, sys, csv
import shutil
import tempfile
import pygit2

# Change these to your own in actual use.
# If using 2FA, PASSWORD must be a personal access token
AUTHOR = "Derpy Hooves"
EMAIL = "derpy@equestria.net"
USERNAME = "muffinsmuffins"
PASSWORD = "ijustd0ntknowwatwentwr0ng"

def clone_destination(owner_name, key):
    """Clone the destination repository given by owner_name.
    key is a RemoteCallbacks object for authentication to GitHub.
    Return a Repository object."""
    name = owner_name.partition("/")[2]
    if os.path.exists(name):
        shutil.rmtree(name)
    git_path = f"https://github.com/{owner_name}.git"
    return pygit2.clone_repository(git_path, name, callbacks=key)

def make_files_folder(repository):
    """Make a folder called files in the given Repository object.
    Return a path to that folder."""
    files_path = os.path.join(repository.workdir, "files")
    os.mkdir(files_path)
    return files_path

def clone_files(name, parent):
    """Clone the named student's PE repository into parent and return
    the path name/files, or None if it does not exist. parent/name
    should not already exist."""
    try:
        git_path = f"git://github.com/{name}/pe.git"
        repo_path = os.path.join(parent, name)
        pygit2.clone_repository(git_path, repo_path)
    except pygit2.GitError: # repository not found
        return None
    files_path = os.path.join(repo_path, "files")
    return files_path if os.path.isdir(files_path) else None

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

def collate_files(names, endpoint):
    """Given a sequence of GitHub usernames of students, clone their
    PE repositories and copy files into endpoint. Return a list of
    duplicate filenames found in the form username/filename."""
    clashes = []
    N = len(names)
    with tempfile.TemporaryDirectory() as tempdir:
        for (n, name) in enumerate(names, 1):
            print(f"{n}/{N} {name}")
            name_path = clone_files(name, tempdir)
            if name_path is None:
                continue
            clashes += transfer_files(name_path, endpoint)
    return [get_user_and_filename(p) for p in clashes]

def commit_repository(repository, author, email, message):
    """Commit the current working state of repository using the given
    author information and message."""
    repository.index.add_all()
    repository.index.write()
    signature = pygit2.Signature(author, email)
    tree = repository.index.write_tree()
    repository.create_commit("HEAD", signature, signature, message,
            tree, [repository.head.target])

def push_repository(repository, key):
    """Push the repository's contents to GitHub with the given key
    (RemoteCallbacks object)."""
    remote = repository.remotes["origin"]
    remote.push(["refs/heads/master"], callbacks=key)

def main():
    """Get the CSV file of students' names and the destination
    repository from the command line, then transfer the files.
    Afterwards, commit and push using author data at the top
    of this module file."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} students.csv owner/name")
        print(f"Example: {sys.argv[0]} fetcher/data.csv nus-cs2103-AY1920S1/pe")
        sys.exit(1)
    __, csv_file, owner_name = sys.argv

    with open(csv_file, 'r') as f:
        students = [row[1] for row in csv.reader(f) if row[0] == "student"]
    user_pass = pygit2.UserPass(USERNAME, PASSWORD)
    key = pygit2.RemoteCallbacks(credentials=user_pass)
    endpoint = clone_destination(owner_name, key)
    files_path = make_files_folder(endpoint)
    clashes = collate_files(students, files_path)
    commit_repository(endpoint, AUTHOR, EMAIL, "Collect PE files")
    push_repository(endpoint, key)

    if clashes:
        print("Files not transferred:")
        for clash in clashes:
            print(clash)

if __name__ == "__main__":
    main()
