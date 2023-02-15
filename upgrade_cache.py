#!/usr/bin/env python3

exit(42)

import datetime
import json
import os
import subprocess
import time

SERENITY_DIR = "serenity/"
FILENAME_CACHE_V2 = "cache_v2.json"
FILENAME_CACHE_V3 = "cache_v3.json"
LAST_COMMIT_BEFORE_DEPRECATEDSTRING = "f74251606d74b504a1379ebb893fdb5529054ea5"
MAGIC_VERSION_KEY = "0000000000000000000000000000000000000000_version"


def determine_usable_commit_list():
    result = subprocess.run(
        [
            "git",
            "-C",
            SERENITY_DIR,
            "log",
            LAST_COMMIT_BEFORE_DEPRECATEDSTRING,
            "--reverse",
            "--format=%H",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.split("\n")
    assert lines[-1] == "", result.stdout[-10:]
    lines.pop()
    assert lines[-1] != "", result.stdout[-10:]
    print(f"Considering only {len(lines)} commits.")
    assert all(len(l) == 40 for l in lines)
    return lines


def run():
    commits = determine_usable_commit_list()
    with open(FILENAME_CACHE_V2, "r") as fp:
        old_cache = json.load(fp)
    assert old_cache[MAGIC_VERSION_KEY] == 2
    new_cache = dict()
    new_cache[MAGIC_VERSION_KEY] = 3
    for commit in commits:
        old_fixmes, old_deprecatedstring = old_cache[commit]
        assert old_deprecatedstring == 0
        new_cache[commit] = [old_fixmes, 0]
    with open(FILENAME_CACHE_V3, "w") as fp:
        json.dump(new_cache, fp, sort_keys=True, separators=",:", indent=0)


if __name__ == "__main__":
    run()
