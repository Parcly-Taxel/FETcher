#!/usr/bin/env python3.7
import os, sys, csv
import shutil
import tempfile
import pygit2

# Change these to your own in actual use.
# If using 2FA, PASSWORD must be a personal access token
AUTHOR_NAME = "Derpy Hooves"
AUTHOR_EMAIL = "derpy@equestria.net"
USERNAME = "muffinsmuffins"
PASSWORD = "ijustd0ntknowwatwentwr0ng"

def clone_files(dst, uname):
    """Clone a student's PE repository into dst and return the path to
    its files directory, or None if said directory does not exist.
    Assumes uname does not already exist in dst."""
    try:
        git_path = f"git://github.com/{uname}/pe.git"
        repo_path = os.path.join(dst, uname)
        repo = pygit2.clone_repository(git_path, repo_path)
    except pygit2.GitError: # repository not found
        return None
    files_path = os.path.join(repo_path, "files")
    return files_path if os.path.isdir(files_path) else None

def transfer_files(src, dst):
    """Transfer all files from src into dst, returning any filenames
    already existing in dst (which are not transferred after
    the first) as a list."""
    dupes = []
    files_in_dst = os.listdir(dst)
    for fn in os.listdir(src):
        fn_full = os.path.join(src, fn)
        if fn in files_in_dst:
            dupes.append(fn_full)
        else:
            shutil.copy(fn_full, dst)
    return dupes

def user_fn(path):
    """Extracts the user and file name from the full paths returned
    from transfer_files()."""
    segs = os.path.normpath(path).split(os.sep)
    return segs[-3] + "/" + segs[-1]

def collate_files(unames, dst):
    """Given a sequence of GitHub usernames, clone the corresponding
    PE repositories and copy files into dst. Return a list of
    duplicate filenames found in the form username/filename."""
    dupes = []
    N = len(unames)
    with tempfile.TemporaryDirectory() as portdir:
        for (n, uname) in enumerate(unames, 1):
            print(f"{n}/{N} {uname}")
            files_path = clone_files(portdir, uname)
            if files_path is None:
                continue
            dupes += transfer_files(files_path, dst)
    return [user_fn(p) for p in dupes]

def main():
    """Get the CSV file of students' names and the destination
    repository from the command line, then transfer the files.
    Afterwards, commit and push using author data at the top
    of this module file."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} students.csv uname/repo")
        print(f"Example: {sys.argv[0]} fetcher/data.csv nus-cs2103-AY1920S1/pe")
        sys.exit(1)
    __, csv_file, dest_repo = sys.argv
    with open(csv_file, 'r') as f:
        students = [row[1] for row in csv.reader(f) if row[0] == "student"]

    uname, rname = dest_repo.split("/")
    if os.path.exists(rname):
        shutil.rmtree(rname)
    git_path = f"https://github.com/{dest_repo}.git"
    creds = pygit2.UserPass(USERNAME, PASSWORD)
    callbacks = pygit2.RemoteCallbacks(credentials=creds)
    dest_repo = pygit2.clone_repository(git_path, rname, callbacks=callbacks)

    dest_path = f"{rname}/files"
    os.mkdir(dest_path)
    dupes = collate_files(students, dest_path)
    # At this point the files have been transferred, so commit them
    dest_repo.index.add_all()
    dest_repo.index.write()
    sig = pygit2.Signature(AUTHOR_NAME, AUTHOR_EMAIL)
    tree = dest_repo.index.write_tree()
    dest_repo.create_commit("HEAD", sig, sig, "Collect PE files",
            tree, [dest_repo.head.target])
    # Push to GitHub
    remote = dest_repo.remotes["origin"]
    remote.credentials = creds
    remote.push(["refs/heads/master"], callbacks=callbacks)

    if dupes:
        print("Files not transferred:")
        for dupe in dupes:
            print(dupe)

if __name__ == "__main__":
    main()
