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
csvfiles = {}
for key in filetypes:
    csvfiles[key] = [tup for tup in zip(
        list(datafolder.glob(
            pattern=f'*/EEG/preprocessed/csv_format/SurroundSupp_Block1_{key}.csv')),
        list(datafolder.glob(
            pattern=f'*/EEG/preprocessed/csv_format/SurroundSupp_Block2_{key}.csv'))
    )]
csvfiles['triggerkeys'] = [tup for tup in zip(
    list(datafolder.glob(
        pattern=f'*/Behavioral/csv_format/*SurroundSupp_Block1.csv')),
    list(datafolder.glob(
        pattern=f'*/Behavioral/csv_format/*SurroundSupp_Block2.csv'))
)]

# add the IDs to this dictionary
csvfiles['id'] = [s[0].parts[-5] for s in csvfiles['chanlocs']]
n = len(csvfiles['id'])


# implement the epoch data structures as a generator
# so that the code isn't run >400x just on import
def epochs():
    for subject in range(len(csvfiles['id'])):

        epochs = []
        badlists = []
        for block in range(2):
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
            badlists.append(
                [ch for b, ch in zip(badbool.ravel(), ch_names) if b]
            )
            # add some cool info
            raw.info['subject_info'] = csvfiles['id'][subject]

            # read the events file and the behav file
            eventdf = pd.read_csv(csvfiles['event'][subject][block])
            decodedf = pd.read_csv(csvfiles['triggerkeys'][subject][block])
            # drop superfluous events
            eventdf = eventdf.loc[eventdf['type'] == '8   ', :]
            # construct a new trigger code:
            eventdf['type'] = np.array(decodedf['BGcon'] * 100 +
                                       decodedf['CNTcon'] * 10 +
                                       decodedf['StimCond'] * 1)
            eventarray = np.array([eventdf.loc[:, 'sample'],
                                   np.zeros(eventdf.shape[0]),
                                   eventdf.loc[:, 'type']],
                                  dtype='int').T

            # make the epoch structure
            epochs.append(mne.Epochs(raw, eventarray, tmin=0, tmax=3))

        badlist = list(set(badlists[0] + badlists[1]))

        epochs[0].info['bads'] = badlist
        epochs[1].info['bads'] = badlist
        # concatenate the two epoch structs since they are equivalent
        epoch = mne.concatenate_epochs(epochs)

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
