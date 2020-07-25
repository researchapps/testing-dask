#!/usr/bin/env python3

# This is an example workflow, created with guidance from
# https://examples.dask.org/applications/evolving-workflows.html
# and with application to process covid data via:
# https://github.com/biglocalnews/covid-world-scraper

from covid_world_scraper import Runner
import os

# No alert manager (e.g., could be slack)
runner = Runner(alert_manager=None)

# runner.list_countries()                                                                                                           
# ['BRA (Brazil)',
# 'DEU (Germany)',
# 'IND (India)',
# 'KOR (South Korea)',
# 'NGA (Nigeria)',
# 'PAK (Pakistan)',
# 'ZAF (South Africa)']

# Set a custom cache directory, run headless, and 
cache_dir = os.path.join(os.getcwd(), 'covid-cache')
if not os.path.exists(cache_dir):
    os.mkdir(cache_dir)

# Testing a single run!
os.environ["PATH"] = "%s:%s" % (os.getcwd(), os.environ["PATH"])
runner.run(cache_dir=cache_dir, headless_status=True, filter=["BRA"])

# This would equivalent to:
# covid-world-scraper --cache-dir=$PWD/covid-cache bra
