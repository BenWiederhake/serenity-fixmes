#!/usr/bin/env python3

exit(42)

import datetime
import json
import os
import subprocess
import time

# V1: Single number for /FIXME|TODO/i
# V2: Two numbers for /FIXME|TODO/i and for /DeprecatedString/i
# V3: Two numbers for /FIXME|TODO/i and for /Deprecated(Fly)?String/i
# V4: Three numbers for /FIXME|TODO/i and for /Deprecated(Fly)?String/ and for /DeprecatedFile/
#     (Note that Deprecated(Fly)?String became case-sensitive, but this does not
#      affect the number of matches as of d7b067e8f7a8c6e52c1b513b8d2a2ded22966376)

SERENITY_DIR = "serenity/"
LAST_COMMIT_BEFORE_DEPRECATEDFILE = "14951b92ca6160664ccb68c5e1b2d40133763e5f"
MAGIC_VERSION_KEY = "0000000000000000000000000000000000000000_version"
MAGIC_VERSION_VALUE_OLD = 3
MAGIC_VERSION_VALUE_NEW = 4
FILENAME_CACHE_OLD = f"cache_v{MAGIC_VERSION_VALUE_OLD}.json"
FILENAME_CACHE_NEW = f"cache_v{MAGIC_VERSION_VALUE_NEW}.json"


def determine_usable_commit_list():
    result = subprocess.run(
        [
            "git",
            "-C",
            SERENITY_DIR,
            "log",
            LAST_COMMIT_BEFORE_DEPRECATEDFILE,
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
    with open(FILENAME_CACHE_OLD, "r") as fp:
        old_cache = json.load(fp)
    assert old_cache[MAGIC_VERSION_KEY] == MAGIC_VERSION_VALUE_OLD
    new_cache = dict()
    new_cache[MAGIC_VERSION_KEY] = MAGIC_VERSION_VALUE_NEW
    for commit in commits:
        old_fixmes, old_deprecatedstring = old_cache[commit]
        new_cache[commit] = [old_fixmes, old_deprecatedstring, 0]
    with open(FILENAME_CACHE_NEW, "w") as fp:
        json.dump(new_cache, fp, sort_keys=True, separators=",:", indent=0)
    print("Writing complete.")


if __name__ == "__main__":
    run()
