from pathlib import Path
import pandas as pd


datafolder = Path('/') / 'Volumes' / 'Seagate Expansion Drive' / 'cmi-hbn'

if not datafolder.exists():
    datafolder = Path('/') / 'Users' / 'jan' / \
        'Documents' / 'eeg-data' / 'cmi-hbn'

if not datafolder.exists():
    # try the windows option
    datafolder = Path('d:') / 'cmi-hbn'

phenotypes = pd.read_csv('data/HBN_S1_Pheno_data.csv')
