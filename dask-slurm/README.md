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

/share/software/user/open/python/3.6.1/bin/python3 -m distributed.cli.dask_worker tcp://10.50.0.64:32978 --nthreads 2 --nprocs 4 --memory-limit 6.00GB --name name --nanny --death-timeout 60 --local-directory /lscratch/vsochat --interface ib0
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
some time.  Now let's try (in a Python session) running dask jobs. I'm not sure this will work
since we are in a different process:

```bash
from dask import array as darr
import numpy as np

xy = darr.random.uniform(
    0, 1,
    size=(1e12 / 16, 2), chunks=(500e6 / 16, None)
)
pi = 4 * ((xy ** 2).sum(-1) < 1).mean()
pi = pi.compute()

print(f"from {xy.nbytes / 1e9} GB of random data:\tpi = {pi}, err = {pi - np.pi}\n")
```

I actually stopped here. It was so slow and annoying just to create the cluster there is no way (if I were a user)
I'd want to go through this. Next, make sure to try killing the process:

```bash
kill -9 444040
```

