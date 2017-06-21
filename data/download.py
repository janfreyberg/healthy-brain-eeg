import boto3
from botocore import UNSIGNED
from botocore.client import Config

from data import datafolder

import requests
import os
import random  # random sampling
from pathlib import Path  # path operations
import shutil  # unzip utils
from tqdm import tqdm  # progress bar

s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

all_remote_files = s3.list_objects(
    Bucket='fcp-indi', Prefix='data/Projects/HBN/S1/EEG/'
)

n_remote = len(all_remote_files['Contents'])

def download_all():
    print(f"Downloading {n_remote} random data sets.")
    for fileobj in tqdm(all_remote_files['Contents'], desc='Files'):
        # request the file
        requests.get(f"https://s3.amazonaws.com/fcp-indi/{fileobj['Key']}",
                     stream=True)
        
        total_length = int(r.headers.get('content-length'))
        
        with open(datafolder / Path(fileobj['Key']).name, 'wb+') as f:
            for chunk in tqdm(r.iter_content(chunk_size=1024),
                              total=(total_length / 1024), desc='Bytes'): 
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)


def download_sample(n=10):
    print(f"Downloading {n} random data sets.")
    for fileobj in tqdm(random.sample(all_remote_files['Contents'], n), desc='Files'):
        # request the file
        r = requests.get(f"http://s3.amazonaws.com/fcp-indi/{fileobj['Key']}",
                         stream=True)
        
        total_length = int(r.headers.get('content-length'))
        
        with open(datafolder / Path(fileobj['Key']).name, 'wb+') as f:
            for chunk in tqdm(r.iter_content(chunk_size=1024),
                              total=(total_length / 1024), desc='Bytes'):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)


def extract_all(delete_archives=True):
    local_archives = list(datafolder.glob(pattern='*.tar.gz'))
    print(f"Extracting {len(local_archives)} files.")
    for f in tqdm(local_archives):
        shutil.unpack_archive(f, datafolder, 'gztar')
        if delete_archives:
            os.remove(f)
