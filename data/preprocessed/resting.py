from pathlib import Path
import os
import numpy as np
import mne
import pandas as pd

# get the data path (not sure this works)
from data import datafolder

# the types of files this dataset has
filetypes = ['chanlocs', 'event', 'data']

# make a list of the resting state files
restfiles = {}
for key in filetypes:
    restfiles[key] = list(datafolder.glob(
        pattern=f'*/EEG/preprocessed/csv_format/RestingState_{key}.csv'
    ))

# add the IDs to this dictionary
restfiles['id'] = [s.parts[-5] for s in restfiles['chanlocs']]


# number of rest files
n = len(restfiles['id'])


# implement the raw data structures as a generator
# so that the code isn't run >400x just on import
def raws():
    for idx in range(len(restfiles['id'])):
        # read the channel locations
        chanlocs = pd.read_csv(restfiles['chanlocs'][idx])
        ch_names = list(chanlocs['labels'])
        pos = np.array(chanlocs.loc[:, ('X', 'Y', 'Z')])
        # make a montage from the chanlocs
        mtg = mne.channels.Montage(
            pos, ch_names, 'custom', range(len(ch_names))
        )
        # make an info structure
        info = mne.create_info(ch_names=ch_names, sfreq=500,
                               ch_types='eeg', montage=mtg)
        # load the data from the text file
        data = np.genfromtxt(restfiles['data'][idx], delimiter=',')
        # find bad electrodes
        badbool = np.all(data == 0, axis=1)
        badlist = [ch for b, ch in zip(badbool.ravel(), ch_names) if b]
        # make the raw data structure
        raw = mne.io.RawArray(data, info)

        # add some cool info
        raw.info['subject_info'] = restfiles['id'][idx]
        raw.info['bads'] = badlist

        yield raw


# make a generator for the events, read from file
def events():
    for idx in range(len(restfiles['id'])):
        # load the events from file
        eventdf = pd.read_csv(restfiles['event'][idx])
        # discard first and last row
        eventdf = eventdf.drop(0)
        eventdf = eventdf.drop(eventdf.tail(1).index)
        # make into n_event x 3 numpy array
        # first col is sample, second is 0, third is event value
        yield np.array([eventdf.loc[:, 'sample'],
                        np.zeros(eventdf.shape[0]),
                        eventdf.loc[:, 'type']],
                       dtype='int').T
