from pathlib import Path
import os
import numpy as np
import mne
import pandas as pd

# get the data path (not sure this works)
from data import datafolder

# the types of files this dataset has
filetypes = ['chanlocs', 'event', 'data']

# make a list of the csv files

datafiles = list(datafolder.glob(
    pattern='*/EEG/preprocessed/csv_format/*SurroundSupp*data.csv'
))
eventfiles = list(datafolder.glob(
    pattern='*/EEG/preprocessed/csv_format/*SurroundSupp*event.csv'
))
chanlocfiles = list(datafolder.glob(
    pattern='*/EEG/preprocessed/csv_format/*SurroundSupp*chanlocs.csv'
))
stimulusfiles = list(datafolder.glob(
    pattern='*/Behavioral/csv_format/*SurroundSupp*.csv'
))

pids = list(set(
    [f.parts[-5] for f in datafiles]
))

datafiles = {
    pid: [f for f in datafiles if pid in f.parts]
    for pid in pids
}
eventfiles = {
    pid: [f for f in eventfiles if pid in f.parts]
    for pid in pids
}
chanlocfiles = {
    pid: [f for f in chanlocfiles if pid in f.parts]
    for pid in pids
}
stimulusfiles = {
    pid: [f for f in stimulusfiles if pid in f.parts]
    for pid in pids
}

# add the IDs to this dictionary
n = len(datafiles)


# implement the epoch data structures as a generator
# so that the code isn't run >400x just on import
def epochs():
    for pid in pids:

        # how many files there are for this subject:
        n_subject = len(datafiles[pid])

        # empty lists for appending
        epochs = []
        badlist = []

        for block in range(n_subject):
            # read the channel locations:
            chanlocs = pd.read_csv(
                chanlocfiles[pid][block]
            )
            ch_names = list(chanlocs['labels'])
            pos = np.array(chanlocs.loc[:, ('X', 'Y', 'Z')])
            # make a montage from the chanlocs
            mtg = mne.channels.Montage(
                pos, ch_names, 'custom', range(len(ch_names))
            )

            # make info structure
            info = mne.create_info(ch_names=ch_names, sfreq=500,
                                   ch_types='eeg', montage=mtg)
            info['subject_info'] = pid

            # load the data from the text file
            data = np.genfromtxt(
                datafiles[pid][block], delimiter=',')
            # make a raw structure
            raw = mne.io.RawArray(data, info)
            # find bad electrodes
            badbool = np.all(data == 0, axis=1)

            badlist = list(set(
                badlist + [ch for b, ch in zip(badbool.ravel(), ch_names)
                           if b]
            ))

            # read the events file and the behav file
            eventdf = pd.read_csv(eventfiles[pid][block])
            decodedf = pd.read_csv(stimulusfiles[pid][block])

            # drop superfluous events
            eventdf = eventdf.loc[eventdf['type'] == '8   ', :]
            # construct a new trigger code:
            eventcode = np.array([cntcon * 100 + bgcon
                                  for cntcon, bgcon in
                                  zip(decodedf['CNTcon'], decodedf['BGcon'])
                                  ])
            eventarray = np.array([eventdf.loc[:, 'sample'],
                                   np.zeros(eventdf.shape[0]),
                                   eventcode],
                                  dtype='int').T

            # make the epoch structure
            epochs.append(mne.Epochs(raw, eventarray, tmin=0, tmax=3))

        # concatenate the two epoch structs since they are equivalent
        epoch = mne.concatenate_epochs(epochs)
        epoch.info['bads'] = badlist

        yield epoch


def raws(block=1):
    for subject in range(len(csvfiles['id'])):
        # read the channel locations:
        chanlocs = pd.read_csv(csvfiles['chanlocs'][subject][block])
        ch_names = list(chanlocs['labels'])
        pos = np.array(chanlocs.loc[:, ('X', 'Y', 'Z')])
        # make a montage from the chanlocs
        mtg = mne.channels.Montage(
            pos, ch_names, 'custom', range(len(ch_names))
        )

        # make info structure
        info = mne.create_info(ch_names=ch_names, sfreq=500,
                               ch_types='eeg', montage=mtg)
        # load the data from the text file
        data = np.genfromtxt(
            csvfiles['data'][subject][block], delimiter=',')
        # make a raw structure
        raw = mne.io.RawArray(data, info)
        # find bad electrodes
        badbool = np.all(data == 0, axis=1)
        raw.info['bads'] = [ch for b, ch in zip(badbool.ravel(), ch_names) if b]
        # add some cool info
        raw.info['subject_info'] = csvfiles['id'][subject]

        yield raw
