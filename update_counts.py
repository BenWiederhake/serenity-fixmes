#!/usr/bin/env python3

import datetime
import json
import os.path
import subprocess
import time

SERENITY_DIR = "/scratch/serenity/"
FILENAME_JSON = "tagged_history.json"
FILENAME_CSV = "tagged_history.csv"
FILENAME_CACHE = "cache.json"
FILENAME_CACHE = "cache_cold.json"
# Save the cache only every X commits, instead of after every commit.
SAVE_CACHE_INV_FREQ = 50


def fetch_new():
    subprocess.run(["git", "-C", SERENITY_DIR, "fetch"], check=True)


def determine_commit_and_date_list():
    result = subprocess.run(
        [
            "git",
            "-C",
            SERENITY_DIR,
            "log",
            "origin/master",
            "--reverse",
            "--format=%H %ct",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.split("\n")
    assert lines[-1] == "", result.stdout[-10:]
    lines.pop()
    assert lines[-1] != "", result.stdout[-10:]
    print(f"Repo has {len(lines)} commits.")
    entries = []
    for line in lines:
        parts = line.split(" ")
        assert len(parts) == 2, line
        entries.append((parts[0], int(parts[1])))
    return entries


def load_cache():
    if not os.path.exists(FILENAME_CACHE):
        with open(FILENAME_CACHE_COLD, "r") as fp:
            cache = json.load(fp)
        # Make sure it's writable:
        save_cache(cache)
    else:
        with open(FILENAME_CACHE, "r") as fp:
            cache = json.load(fp)
    return cache


def save_cache(cache):
    with open(FILENAME_CACHE, "w") as fp:
        json.dump(cache, fp, sort_keys=True, separators=",:")


def count_fixmes(commit):
    subprocess.run(["git", "-C", SERENITY_DIR, "checkout", "-q", commit], check=True)
    # We don't use "-n" here, since we don't use that information, and less output should make it marginally faster.
    result = subprocess.run(
        ["git", "-C", SERENITY_DIR, "grep", "-iE", "FIXME|TODO"],
        check=True,
        capture_output=True,
        text=True,
    )
    lines = result.stdout.split("\n")
    assert lines[-1] == "", result.stdout[-10:]
    return len(lines)


def lookup_commit(commit, date, cache):
    if commit in cache:
        fixmes = cache[commit]
    else:
        time_start = time.time()
        fixmes = count_fixmes(commit)
        time_done_counting = time.time()
        cache[commit] = fixmes
        if len(cache) % SAVE_CACHE_INV_FREQ == 0:
            print("    (actually saving cache)")
            save_cache(cache)
        time_done_saving = time.time()
        print(
            f"Extended cache by {commit} (now containing {len(cache)} keys) (counting took {time_done_counting - time_start}s, saving took {time_done_saving - time_done_counting}s)"
        )
    human_readable_time = datetime.datetime.fromtimestamp(date).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return dict(
        commit=commit,
        unix_timestamp=date,
        human_readable_time=human_readable_time,
        fixmes=fixmes,
    )


def run():
    fetch_new()
    commits_and_dates = determine_commit_and_date_list()
    print(f"Newest commits are: ...{commits_and_dates[-3 :]} (time is {time.time()})")
    cache = load_cache()
    tagged_commits = [
        lookup_commit(commit, date, cache) for commit, date in commits_and_dates[:20000]
    ]
    save_cache(cache)
    # with open(FILENAME_JSON, "w") as fp:
    #     json.dump(tagged_commits, fp, sort_keys=True, indent=1)
    with open(FILENAME_CSV, "w") as fp:
        for entry in tagged_commits:
            fp.write(f"{entry['unix_timestamp']},{entry['fixmes']}\n")
    # FIXME: make_graph(tagged_commits)


if __name__ == "__main__":
    run()
