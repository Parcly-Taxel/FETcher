#!/usr/bin/env python3.7
import os, csv, shutil
import pygit2

def collate_pe_images(unames, dest):
    """Given a sequence of GitHub usernames, clone the corresponding
    PE repositories and copy image files into dest. Return a list of
    all collisions (duplicate filenames after the first instance)
    in the form username/filename.
    
    Only the first instance of a given filename is copied, and
    repositories are deleted after their files are transferred."""
    copied_fns = set()
    collisions = []

    for uname in unames:
        if os.path.exists(uname): # ensure the repository can be cloned
            shutil.rmtree(uname)
        try:
            git_path = f"git://github.com/{uname}/pe.git"
            repo = pygit2.clone_repository(git_path, uname)
        except pygit2.GitError: # repository not found
            continue

        files = os.path.join(uname, "files")
        if os.path.exists(files):
            for fn in os.listdir(files):
                if fn in copied_fns:
                    collisions += f"{uname}/{fn}"
                else:
                    shutil.copy(os.path.join(files, fn), dest)
                    copied_fns.add(fn)
        shutil.rmtree(uname) # keep current folder clean
    return collisions

with open("data.csv", 'r') as f:
    names = [row[1] for row in csv.reader(f) if row[0] == "student"]
collate_pe_images(names, "comb")
