# Testing Dask

I want to test Dask, intending to create a small dask cluster for SLURM
to submit jobs with via Airflow (possibly via the Singularity operator).
Notice that there [aren't any slurm executors](https://github.com/apache/airflow/tree/master/airflow/executors), 
and I suspect this is because Dask can be used as a wrapper to slurm.

 - [1. Local Testing with Dask + Apache Airflow](dask-airflow-local): I wanted to see if the Airflow + Dask executor would be easy to spin up to run a simple DAG. It was complex and error prone enough that I wouldn't recommend this approach to a researcher.
 - [2. Local Testing with Dask](dask-local): Sometimes a good strategy when developing a plan is to simplify. So for this test case, I want to again test Dask locally, but throw away Airflow. Does the dask dashboard, and dask alone, provide enough functionality to run and monitor my jobs?
