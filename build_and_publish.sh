#!/bin/sh

set -ex

SOURCES="\
    output_total.png
    output_day.png
    output_week.png
    output_month.png
    output_year.png
    tagged_history.json
    tagged_history.csv
    cache.json
    index.html
    flamegraph.html
    loc.json
    todo.json
    d3_LICENSE.txt
    d3-flamegraph.min.js
    d3-flamegraph_4.1.3.css
    d3.v7.7.0.min.js
"

cd -P -- "$(dirname -- "$0")"
python3.10 ./update_counts.py
cp -t pages/ ${SOURCES}
cd pages
git add ${SOURCES}
git commit -m "Automatic update" --amend
git push -f
