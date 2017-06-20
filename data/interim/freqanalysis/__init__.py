import numpy as np
import pickle
import mne
from pathlib import Path


picklefolder = Path('data') / 'interim' / 'freqanalysis'



# This generator will produce the freq and psd for each of the pickle files in this folder
def psds(recording = 'rest'):
    picklefiles = picklefolder.glob(pattern = recording + '*.pickle')
    # load the data and yield it
    for file in picklefiles:
        pid = file.name[5:17]
        with open(file, 'rb') as f:
            freq, psd = pickle.load(f)
            yield pid, freq, psd