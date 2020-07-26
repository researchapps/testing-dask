#!/usr/bin/env python3

from prefect.engine.executors import DaskExecutor
from prefect import task, Flow, unmapped
from covid_world_scraper import Runner
import os
import sys

# Instantiate the executor (this can come from environment if needed)
executor = DaskExecutor(address="tcp://127.0.0.1:8786")

here = os.path.dirname(os.path.abspath(__file__))

@task(name="create_cachedir")
def create_cachedir():
    """Set a custom cache directory, done before workflow submit
    """
    cache_dir = os.path.join(here, 'covid-cache')
    if not os.path.exists(cache_dir):
        os.mkdir(cache_dir)
    return os.path.abspath(cache_dir)

@task
def process_data(country, cache_dir):
    """the main function to instantiate a runner, and process data
    """    
    # No alert manager (e.g., could be slack)
    runner = Runner(alert_manager=None)

    # Make sure geckodriver is on the path
    os.environ["PATH"] = "%s:%s" % (os.getcwd(), os.environ["PATH"])

    # This would equivalent to:
    # covid-world-scraper --cache-dir=$PWD/covid-cache bra
    print(f"Processing {country}")
    runner.run(cache_dir=cache_dir, headless_status=True, filter=[country])


@task(name="list_countries")
def list_countries():
    """Return list of all countries available, which will be mapped to the
       process data function (to run in parallel if possible).
    """
    runner = Runner(alert_manager=None)
    return [x.split(' ')[0] for x in runner.list_countries()]


with Flow("dask-example") as flow:
    cache_dir = create_cachedir()
    countries = list_countries()
    process_data.map(country=countries, cache_dir=unmapped(cache_dir))

# Run and visualize the flow!
flow_state = flow.run(executor=executor)

# GraphViz is required for this visualization
try:
    flow.visualize(flow_state=flow_state) 
except Exception as err:
    print(err)
