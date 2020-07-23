# Testing Dask

I want to test Dask, intending to create a small dask cluster for SLURM
to submit jobs with via Airflow (possibly via the Singularity operator).
Notice that there [aren't any slurm executors](https://github.com/apache/airflow/tree/master/airflow/executors), 
and I suspect this is because Dask can be used as a wrapper to slurm.

## Local Testing

### 1. Prepare Local Environment

First let's test this locally! If it works locally, then it's reasonable to try
on the cluster. Let's first install our requirements - namely dask and airflow.

```bash
python -m venv env
source env/bin/activate
pip install  -r requirements.txt
```

### 2. Start dask client

Airflow seems to want to interact with a [Dask client](https://airflow.apache.org/docs/1.10.5/howto/executor/use-dask.html), 
so let's start that first. Here is how we might do it in Python:

```python
from dask.distributed import Client, progress
client = Client(processes=False, threads_per_worker=4,
                n_workers=1, memory_limit='2GB')
client
# <Client: 'inproc://192.168.82.244/1470/1' processes=1 threads=4, memory=2.00 GB>
```

You could then see the dashboard at [http://192.168.82.244:8787/status](http://192.168.82.244:8787/status).
And here is how to do it from the command line. The `dask-scheduler` executable should
be available when you install dask and source the virtual environment.

```bash
# default settings for a local cluster
DASK_HOST=127.0.0.1
DASK_PORT=8786

$ dask-scheduler --host $DASK_HOST --port $DASK_PORT &
distributed.scheduler - INFO - -----------------------------------------------
distributed.http.proxy - INFO - To route to workers diagnostics web server please install jupyter-server-proxy: python -m pip install jupyter-server-proxy
distributed.scheduler - INFO - -----------------------------------------------
distributed.scheduler - INFO - Clear task state
distributed.scheduler - INFO -   Scheduler at:      tcp://127.0.0.1:8786
distributed.scheduler - INFO -   dashboard at:            127.0.0.1:8787
[1] 2131
```

Keep track of the pid so you can kill the scheduler later. Now start a worker,
and do the same:

```bash
$ dask-worker $DASK_HOST:$DASK_PORT &
[1] 2506
```

Now we want to test control and submission via airflow.

### 3. Airflow

Before we start airflow, let's change `AIRFLOW_HOME` so we can write the config
file in our present working directory.

```bash
export AIRFLOW_HOME=$PWD
```

Now ensure that airflow is on your path:

```bash
$ which airflow 
/home/vanessa/Desktop/Code/test-dask/env/bin/airflow
```

And run `airflow initdb` to initialize a small sqlite database is the present working
directory, along with your [airflow.cfg](airflow.cfg) file. 

Note that after we initialize it, we edit it so specify a DaskExecutor:

```
# The executor class that airflow should use. Choices include
# SequentialExecutor, LocalExecutor, CeleryExecutor, DaskExecutor, KubernetesExecutor
executor = DaskExecutor
```

and the default local address under `[dask]` is correct (you don't need to edit this):

```
[dask]

# This section only applies if you are using the DaskExecutor in
# [core] section above
# The IP address and port of the Dask cluster's scheduler.
cluster_address = 127.0.0.1:8786
```

Now we want to test submitting a job! But when we start the scheduler, we get this
error message:

```bash
airflow scheduler
...
airflow.exceptions.AirflowConfigException: error: cannot use sqlite with the DaskExecutor
```

### 4. Docker Compose Database

This might be an issue for running on the cluster, but let's assume we can ask for Stanford
managed SQL, and that we can (for now) run a Docker container for a throw away database.
First, copy the [.env-example](.env-example) file and change the variables to something
secret for you to use.

```bash
cp .env-example env
source .env
```

Then build the container. The [docker-compose.yml](docker-compose.yml) file
included here will source the environment file named `.env`.

```bash
docker-compose up -d
```

Make sure it's running as expected without any error exit codes:

```bash
$ docker-compose ps
   Name                 Command               State                 Ports              
---------------------------------------------------------------------------------------
airflow_db   docker-entrypoint.sh mysql ...   Up      0.0.0.0:3306->3306/tcp, 33060/tcp
```

We now need to tell airflow to use our database. Comment out the last line here in your airflow.cfg:

```
# The SqlAlchemy connection string to the metadata database.
# SqlAlchemy supports many different database engine, more information
# their website
# sql_alchemy_conn = sqlite:////home/vanessa/Desktop/Code/test-dask/airflow.db
```

And now we can export the environment variable with our secrets for airflow to find:

```bash
export AIRFLOW__CORE__SQL_ALCHEMY_CONN="mysql://${MYSQL_USER}:${MYSQL_PASSWORD}@127.0.0.1/airflow"
export AIRFLOW_CONN_DEV_DATABASE="mysql://${MYSQL_USER}:${MYSQL_PASSWORD}@127.0.0.1:3306/airflow"
```

And note that we will also need native bindings for mysql. I suspect these would
be loadable on Sherlock.

```bash
sudo apt-get install -y libmysqlclient-dev
pip install mysqlclient
```

Once we've updated the connection strings above, we need to run initdb again.

```bash
airflow initdb
```

Then try creating the connection again (running in background, we will kill pids later)

```bash
airflow scheduler &
  ____________       _____________
 ____    |__( )_________  __/__  /________      __
____  /| |_  /__  ___/_  /_ __  /_  __ \_ | /| / /
___  ___ |  / _  /   _  __/ _  / / /_/ /_ |/ |/ /
 _/_/  |_/_/  /_/    /_/    /_/  \____/____/|__/
[2020-07-23 14:09:26,912] {__init__.py:50} INFO - Using executor DaskExecutor
[2020-07-23 14:09:26,916] {scheduler_job.py:1349} INFO - Starting the scheduler
[2020-07-23 14:09:26,916] {scheduler_job.py:1357} INFO - Running execute loop for -1 seconds
[2020-07-23 14:09:26,916] {scheduler_job.py:1358} INFO - Processing each file at most -1 times
[2020-07-23 14:09:26,917] {scheduler_job.py:1361} INFO - Searching for files in /home/vanessa/Desktop/Code/test-dask/dags
[2020-07-23 14:09:26,918] {scheduler_job.py:1363} INFO - There are 25 files in /home/vanessa/Desktop/Code/test-dask/dags
distributed.scheduler - INFO - Receive client connection: Client-68cea928-cd20-11ea-983f-bfc14111f66d
distributed.core - INFO - Starting established connection
[2020-07-23 14:09:26,930] {scheduler_job.py:1420} INFO - Resetting orphaned tasks for active dag runs
[2020-07-23 14:09:26,938] {dag_processing.py:562} INFO - Launched DagFileProcessorManager with pid: 6221
[2020-07-23 14:09:26,940] {settings.py:55} INFO - Configured default timezone <Timezone [UTC]>
[3] 6400
```

And start the webserver, and open up to localhost:8080 to enable the local DAG.

```bash
$ airflow webserver -p 8080 &
[4] 6536
```

You can then enable the example bash operator, and even take a look! 

![img/enable-bash-operator.png](img/enable-bash-operator.png)

I would also check out the Code view so you can see that a Dag is just a Python file :)

![img/dag.png](img/dag.png)

Then run the job from the command line:

```bash
$ airflow run example_bash_operator runme_0 2015-01-01
```

I didn't get this working, and given the complexity of setup I'm not sure I'd recommend
this for running workflows on HPC. I want to test Dask without airflow next, and
compare that to snakemake (also python). Don't forget to cleanup.

```bash
docker-compose stop
```

## Slurm Testing

**not tested because local not optimal**

```bash
from dask_jobqueue import SLURMCluster
from distributed import Client
from dask import delayed

cluster = SLURMCluster(memory='8g',
                       processes=1,
                       cores=2,
                       extra=['--resources ssdGB=200,GPU=2'])

cluster.start_workers(2)
client = Client(cluster)
```
