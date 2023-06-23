#! /usr/bin/bash
wc -l data/extract_addresses_*.csv | sort -n -r | grep ....csv -o | sed 's/.csv//' | \
  parallel -j 40 -t  python 1_geocode_reu.py extract_addresses_{}.csv \> data/log/extract_addresses_{}.log
  