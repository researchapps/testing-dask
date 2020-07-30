from dask.distributed import Client
from dask import array as darr
import numpy as np

cluster_address = 'tcp://10.18.1.58:38211'  # obtained from previous script
client = Client(cluster_address)

xy = darr.random.uniform(
    0, 1,
    size=(1e12 / 16, 2), chunks=(500e6 / 16, None)
)
pi = 4 * ((xy ** 2).sum(-1) < 1).mean()
pi = pi.compute()

print(f"from {xy.nbytes / 1e9} GB of random data:\tpi = {pi}, err = {pi - np.pi}\n")
