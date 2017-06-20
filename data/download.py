import boto3
from botocore import UNSIGNED
from botocore.client import Config

from data import datafolder

import random  # random sampling
from pathlib import Path  # path operations
import shutil  # unzip
from tqdm import tqdm  # progress bar

s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

all_remote_files = s3.list_objects(Bucket='fcp-indi',
                                   Prefix='data/Projects/HBN/S1/EEG/')


def download_all():
    for fileobj in tqdm(all_remote_files['Contents']):
        s3.download_file('fcp-indi', fileobj['Key'],
                         str(datafolder / Path(fileobj['Key']).name))


def download_sample(n=10):
    for fileobj in tqdm(random.sample(all_remote_files['Contents'], n)):
        s3.download_file('fcp-indi', fileobj['Key'],
                         str(datafolder / Path(fileobj['Key']).name))


def extract_all():
    local_archives = list(datafolder.glob(pattern='*.tar.gz'))
    for f in tqdm(local_archives):
        shutil.unpack_archive(f, datafolder, 'gztar')
