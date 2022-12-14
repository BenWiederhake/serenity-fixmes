#!/bin/sh

set -ex

cd -P -- "$(dirname -- "$0")"
python3.10 ./update_counts.py
cp -t pages/ output_total.png  output_day.png  output_week.png  output_month.png  output_year.png tagged_history.json tagged_history.csv cache.json
cd pages
git add output_total.png  output_day.png  output_week.png  output_month.png  output_year.png tagged_history.json tagged_history.csv cache.json
git commit -m "Automatic update" --amend
git push -f
