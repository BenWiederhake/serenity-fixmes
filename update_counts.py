#!/usr/bin/env python3

# There are about 2000 commits in a month, in the recent time.
# That's about 60 commits per day.
# 1 second per grep invocation would be quite slow, let's assume that.
# The other parts of this script are negligible.
# So this script consumes about 1 minute of CPU time per day.
# That's acceptable. (Less pessimistic numbers predict about 15 seconds per day.)

import datetime
import json
import os
import subprocess
import time

SERENITY_DIR = "serenity/"
FILENAME_JSON = "tagged_history.json"
FILENAME_CSV = "tagged_history.csv"
FILENAME_CACHE = "cache.json"
FILENAME_CACHE_COLD = "cache_cold.json"
# Save the cache only every X commits, instead of after every commit.
SAVE_CACHE_INV_FREQ = 50
# *Some* versions of gnuplot use year 2000 as epoch, and in those versions *only*
# the xrange is interpreted relative to this. Aaargh!
GNUPLOT_STUPIDITY = 946684800


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
        json.dump(cache, fp, sort_keys=True, separators=",:", indent=0)


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


def write_graphs(most_recent_commit):
    time_now = int(time.time())
    print(f"Plotting with {time_now=}")
    time_yesterday = time_now - 3600 * 24
    time_last_week = time_now - 3600 * 24 * 7
    time_last_month = time_now - 3600 * 24 * 31  # All months are 31 days. Right.
    time_last_year = time_now - 3600 * 24 * 366  # All years are 366 days. Right.
    timed_plot_commands = ""
    if most_recent_commit > time_yesterday:
        timed_plot_commands += f"""
            set output "output_day.png"; plot [{time_yesterday - GNUPLOT_STUPIDITY}:{time_now - GNUPLOT_STUPIDITY}] "tagged_history.csv" using 1:2 with lines;
        """
    if most_recent_commit > time_last_week:
        timed_plot_commands += f"""
            set output "output_week.png"; plot [{time_last_week - GNUPLOT_STUPIDITY}:{time_now - GNUPLOT_STUPIDITY}] "tagged_history.csv" using 1:2 with lines;
        """
    if most_recent_commit > time_last_month:
        timed_plot_commands += f"""
            set output "output_month.png"; plot [{time_last_month - GNUPLOT_STUPIDITY}:{time_now - GNUPLOT_STUPIDITY}] "tagged_history.csv" using 1:2 with lines;
        """
    if most_recent_commit > time_last_year:
        timed_plot_commands += f"""
            set output "output_year.png"; plot [{time_last_year - GNUPLOT_STUPIDITY}:{time_now - GNUPLOT_STUPIDITY}] "tagged_history.csv" using 1:2 with lines;
        """
    subprocess.run(
        [
            "gnuplot",
            "-e",
            f"""
                set terminal png size 1700,900 enhanced;
                set xdata time;
                set timefmt "%s";
                set xlabel "Time";
                set format x "%Y-%m-%d %H:%M";
                set ylabel "Fixmes and todos";
                set datafile separator ",";
                set output "output_total.png";
                plot "tagged_history.csv" using 1:2 with lines;
                {timed_plot_commands}
            """,
        ],
        check=True,
    )


def generate_flame_graph():
    flamegraph = {"name": ".", "children":[]}

    def get_node(path):
        node = flamegraph
        for f in os.path.normpath(path).split(os.path.sep):
            if f in [".git", ".devcontainer"]:
                return None
            if "children" not in node:
                node["children"] = []
            for child in node["children"]:
                if child["name"] == f:
                    node = child
                    break
            else:
                new_node = {"name" : f}
                node["children"].append(new_node)
                node = new_node
        return node

    previous_wd = os.getcwd()
    os.chdir(SERENITY_DIR)

    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            if not any(name.endswith(ext) for ext in [".h", ".c", ".cpp", ".html", ".js", ".sh", "*.txt", "*.cmake"]):
                continue
            node = get_node(os.path.join(root, name))
            if not node:
                continue
            todos = 0
            locs = 0
            with open(os.path.join(root, name), "rt") as f:
                for line in f:
                    line = line.strip().upper()
                    todos += line.count("FIXME") + line.count("TODO")
                    if line and not line.startswith("//"):
                        locs += 1
            node["todos"] = todos
            node["locs"] = locs

        for name in dirs:
            node = get_node(os.path.join(root, name))
            if not node:
                continue
            todos = 0
            locs = 0
            for c in node.get("children", []):
                todos += c["todos"]
                locs += c["locs"]
            node["todos"] = todos
            node["locs"] = locs
    os.chdir(previous_wd)

    def set_value(calculate, node=flamegraph):
        node["value"] = calculate(node)
        for c in node.get("children", []):
            set_value(calculate, c)

    set_value(lambda node: node.get("todos", 0))
    with open("todo.json", "wt") as file:
        json.dump(flamegraph, file)

    set_value(lambda node: node.get("locs", 0))
    with open("loc.json", "wt") as file:
        json.dump(flamegraph, file)


def run():
    if not os.path.exists(SERENITY_DIR + "README.md"):
        print(
            f"Can't find Serenity checkout at {SERENITY_DIR} , please make sure that a reasonably recent git checkout is at that location."
        )
        exit(1)
    fetch_new()
    commits_and_dates = determine_commit_and_date_list()
    print(f"Newest commits are: ...{commits_and_dates[-3 :]}")
    current_time = int(time.time())
    print(
        f"(The time is {current_time}, the last commit is {current_time - commits_and_dates[-1][1]}s ago)"
    )
    cache = load_cache()
    tagged_commits = [
        lookup_commit(commit, date, cache) for commit, date in commits_and_dates
    ]
    save_cache(cache)
    with open(FILENAME_JSON, "w") as fp:
        json.dump(tagged_commits, fp, sort_keys=True, indent=1)
    with open(FILENAME_CSV, "w") as fp:
        for entry in tagged_commits:
            fp.write(f"{entry['unix_timestamp']},{entry['fixmes']}\n")
    write_graphs(commits_and_dates[-1][1])

    generate_flame_graph()


if __name__ == "__main__":
    run()
