# Dask + SLURM

This is inspired by [this notebook](https://gist.github.com/willirath/2176a9fa792577b269cb393995f43dda). We should be able
to accomplish something similar (I hope!). Note that I did try to do this via an OnDemand notebook,
but it didn't work.

## Test Case 3: Dask + Slurm

Let's start a screen that will keep our cluster running first:

```bash
screen
```

and then load the python we want:

```bash
module load python/3.6.1
```

Install dask dependencies:

```bash
pip install dask[complete] dask_jobqueue
```

Next let's write a script 

```python
from dask_jobqueue import SLURMCluster
from dask.distributed import Client
import os

cluster = SLURMCluster(queue='owners',
                       cores=8, 
                       memory="24GB", 
                       walltime="00:20:00",
                       interface="ib0",
                       local_directory=os.environ.get("LOCAL_SCRATCH"))

print(cluster)
# SLURMCluster('tcp://10.18.1.58:38211', workers=0, threads=0, memory=0 B)
print(cluster.job_script())
#!/usr/bin/env bash
#SBATCH -J dask-worker
#SBATCH -p owners
#SBATCH -n 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=23G
#SBATCH -t 00:20:00

# /share/software/user/open/python/3.6.1/bin/python3 -m distributed.cli.dask_worker tcp://10.50.0.64:32978 --nthreads 2 --nprocs 4 --memory-limit 6.00GB --name name --nanny --death-timeout 60 --local-directory /lscratch/vsochat --interface ib0
cluster.scale(4)
print(cluster)
while True:
    pass
```

Then run! Make sure to get the pid of the cluster so you can kill it later:

```bash
$ python3 run_dask.py &
[1] 444040
```

And keep in mind that you are submitting jobs to the queue, so that line (cluster.scale) might take
some time.  Now let's try (in a Python session) running dask jobs. We have to instantiate the
correct client since it's running in a different process (see [run_job.py](run_job.py)). This
took a fairly long time for me, I'm not sure it was correctly using my cluster, or maybe my 
cluster was too small.

So this worked okay when I just asked for one node, but scaling beyond that it was never able
to get through the script to create the allocation for dask workers. If I were a user I'm not sure
this would be significantly easier or better than just submitting jobs. The issue is that we don't just
want another tool, we want one that has a beautiful interface and ability to click and interact.
Dask and Airflow have seemed like good contenders for that, but getting this running in a headless
environment is consistently a pain. Next, make sure to try killing the process:

```bash
kill -9 444040
```

## Test Case 4: Dask-mpi + Slurm

It was suggested to try out [dask-mpi](http://mpi.dask.org/en/latest/) as a more suitable
model to run jobs on our cluster. We are again on screen using a head node for our cluster, and we can install
it:

```bash
pip install dask_mpi
```

And load mpi:

```bash
module load openmpi/4.0.3
module load python/3.6.1
```

Check that it was added to your path!

```bash
$ which mpirun
/share/software/user/open/openmpi/4.0.3/bin/mpirun
```

The only version of mpi4py on the cluster is for Python 2, so let's install an updated one for Python 3:

```bash
pip install mpi4py
```

It's next good to then check that dask-mpi is also on the path (it wasn't in my case). If it's on your path
you can just do:

```bash
mpirun -np 4 dask-mpi
```

But I needed to run:

```bash
mpirun -np 4 ./.local/bin/dask-mpi
```

This led to an error I'd seen before:

```bash
    raise TypeError("addresses should be strings or tuples, got %r" % (addr,))
TypeError: addresses should be strings or tuples, got None
distributed.nanny - INFO - Closing Nanny at 'tcp://171.66.103.154:46493'
distributed.nanny - INFO - Closing Nanny at 'tcp://171.66.103.154:37182'
```

I decided to test running on a development node instead:

```bash
srun --partition dev --ntasks 2 --pty bash
module load openmpi/4.0.3
module load python/3.6.1
mpirun -np 2 ./.local/bin/dask-mpi
```

That worked slightly better, but not really.

```
distributed.nanny - INFO -         Start Nanny at: 'tcp://10.18.1.57:33030'
--------------------------------------------------------------------------
It looks like orte_init failed for some reason; your parallel process is
likely to abort.  There are many reasons that a parallel process can
fail during orte_init; some of which are due to configuration or
environment problems.  This failure appears to be an internal failure;
here's some additional information (which may only be relevant to an
Open MPI developer):

  getting local rank failed
  --> Returned value No permission (-17) instead of ORTE_SUCCESS
--------------------------------------------------------------------------
--------------------------------------------------------------------------
It looks like orte_init failed for some reason; your parallel process is
likely to abort.  There are many reasons that a parallel process can
fail during orte_init; some of which are due to configuration or
environment problems.  This failure appears to be an internal failure;
here's some additional information (which may only be relevant to an
Open MPI developer):

  orte_ess_init failed
  --> Returned value No permission (-17) instead of ORTE_SUCCESS
--------------------------------------------------------------------------
--------------------------------------------------------------------------
It looks like MPI_INIT failed for some reason; your parallel process is
likely to abort.  There are many reasons that a parallel process can
fail during MPI_INIT; some of which are due to configuration or environment
problems.  This failure appears to be an internal failure; here's some
additional information (which may only be relevant to an Open MPI
developer):

  ompi_mpi_init: ompi_rte_init failed
  --> Returned "No permission" (-17) instead of "Success" (0)
--------------------------------------------------------------------------
*** An error occurred in MPI_Init_thread
*** on a NULL communicator
*** MPI_ERRORS_ARE_FATAL (processes in this communicator will now abort,
***    and potentially your MPI job)
[sh02-01n57.int:73239] Local abort before MPI_INIT completed completed successfully, but am not able to aggregate error messages, and not able to guarantee that all other processes were killed!
distributed.nanny - INFO - Worker process 73239 exited with status 1
distributed.nanny - INFO - Closing Nanny at 'tcp://10.18.1.57:33030'
distributed.nanny - INFO - Closing Nanny at 'tcp://10.18.1.57:33030'
distributed.http.proxy - INFO - To route to workers diagnostics web server please install jupyter-server-proxy: python -m pip install jupyter-server-proxy
distributed.scheduler - INFO - Clear task state
distributed.scheduler - INFO -   Scheduler at:    tcp://10.18.1.57:32803
distributed.scheduler - INFO -   dashboard at:                     :8787
```

I'm having a very hard time seeing how this could make my cluster life easier, but
of course I'll try again if there are other suggestions!
