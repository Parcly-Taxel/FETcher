#!/usr/bin/env python3.7
import os, sys, csv
import shutil
import tempfile
import pygit2

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
            dupes += fn_full
            print(fn_full)
        else:
            shutil.copy(fn_full, dst)
    return dupes

def collate_files(unames, dst):
    """Given a sequence of GitHub usernames, clone the corresponding
    PE repositories and copy files into dst. Return a list of
    duplicate filenames found in the form username/filename."""
    dupes = []
    N = len(unames)
    with tempfile.TemporaryDirectory() as portdir:
        for (n, uname) in enumerate(unames, 1):
            # XXX remove when completed!
            if n > 10:
                break
            print(f"{n}/{N} {uname}")
            files_path = clone_files(portdir, uname)
            if files_path is None:
                continue
            dupes += transfer_files(files_path, dst)
    return dupes

def main():
    """Get CSV file of students' names and destination repository
    from the command line, then transfer the files."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} students.csv uname/repo")
        print(f"Example: {sys.argv[0]} fetcher/data.csv kennethreitz/samplemod")
        sys.exit(1)
    __, csv_file, dest_repo = sys.argv
    with open(csv_file, 'r') as f:
        students = [row[1] for row in csv.reader(f) if row[0] == "student"]

    uname, rname = dest_repo.split("/")
    if os.path.exists(rname):
        shutil.rmtree(rname)
    git_path = f"git://github.com/{dest_repo}.git"
    dest_repo = pygit2.clone_repository(git_path, rname)

    dest_path = f"{rname}/files"
    # os.mkdir(dest_path)
    dupes = collate_files(students, dest_path)
    # At this point the files have been transferred.
    # TODO commit and push
    return dupes

if __name__ == "__main__":
    main()
