#!/bin/sh

set -ex

SOURCES="\
    output_total.png
    output_week.png
    output_month.png
    output_year.png
    output_total_depstr.png
    output_week_depstr.png
    output_month_depstr.png
    output_year_depstr.png
    output_total_depfil.png
    output_week_depfil.png
    output_month_depfil.png
    output_year_depfil.png
    tagged_history.json
    tagged_history.csv
    cache_v3.json
    index.html
    flamegraph.html
    loc.json
    todo.json
    d3_LICENSE.txt
    d3-flamegraph.min.js
    d3-flamegraph_4.1.3.css
    d3.v7.7.0.min.js
    ratio.csv
    jquery_LICENSE.txt
    jquery-3.6.0.slim.min.js
    datatables_LICENSE.txt
    jquery.dataTables.min.css
    jquery.dataTables.min.js
"

cd -P -- "$(dirname -- "$0")"
python3.10 ./update_counts.py
cp -t pages/ ${SOURCES}
cd pages
git add ${SOURCES}
git commit -m "Automatic update" --amend
git push -f
