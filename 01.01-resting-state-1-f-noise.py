
# coding: utf-8

# # Resting state analysis

# In[8]:

import pickle
from pathlib import Path
import os

import mne

import numpy as np
import scipy.stats

import matplotlib as mpl
import matplotlib.pyplot as plt
try:
    get_ipython().magic('matplotlib inline')
except:
    pass

import pandas as pd

from tqdm import tqdm as tqdm


# ## Take the raw data and frequency-transform it
# 
# In this package I have already made scripts that effectively turn the CSV files into raw files using a generator function: `restraws()`. You can find that [here](data/processed/resting.py). It doesn't do anything other than: 1) load the data from CSV; 2) load the channel locations; 3) combine the two to make a neat [`Raw`](http://martinos.org/mne/dev/generated/mne.io.Raw.html) data with a proper montage, all zero-channels set as `bads`, and the subject's name in the info structure. The neat thing is that it does it _on each iteration_, so it loads the data one by one, and removes it from memory when the next one comes up.
# 
# Here, I'm going to load that data, then average-ref it and do a time-frequency transform on it. This is already effectively preprocessed. The time-frequency data is saved to the data/interim/freqanalysis.

# In[ ]:

from data.processed.resting import restraws, restevents, nrest

for raw in restraws():
    
    # output names
    psdfname = (Path('.') / 'data' / 'interim' / 'freqanalysis' /
                ('rest-' + raw.info['subject_info'] + '.pickle'))
    infofname = (Path('.') / 'data' / 'interim' / 'info' /
                 ('rest-' + raw.info['subject_info'] + '.pickle'))
    
    # save the info structure to file (incl bads)
    with open(infofname, 'wb+') as f:
        pickle.dump(raw.info, f)
    
    # if it exists already, skip
    if os.path.isfile(psdfname): continue
        
    # try cropping it; this will fail if less than 200s; so skip
    try:
        raw.crop(tmin=0, tmax=200)
    except ValueError:
        continue
    
    # average reference
    raw.set_eeg_reference()
    raw.apply_proj()
    
    # do the time-frequency analysis
    psd, freqs = mne.time_frequency.psd_multitaper(raw, fmin=1, fmax=30, n_jobs=4)
    
    # save TFR and Info to pickle
    with open(psdfname, 'wb+') as f:
        pickle.dump((freqs, psd), f)



# ## Load the data back from pickle
# 
# In `data/interim/freqanalysis` [another python script](data/interim/freqanalysis/__init__.py) sits that lets you load the data __back__ into memory via a generator. So here I do that, then fit the linear regression in semilog and loglog space.

# In[6]:

from data.interim.freqanalysis import psds
import scipy.stats

alldata = []

for pid, freq, psd in psds():
    
    # identify the right frequency band
    idx = ((freq > 4) & (freq < 7)) | ((freq > 14) & (freq < 24))
    
    # fit linear regression in semilog space
    semilogfits = [scipy.stats.linregress(freq[idx], np.log10(psd.T[idx, sensor]))
                      for sensor in range(psd.shape[0])]
    loglogfits  = [scipy.stats.linregress(np.log10(freq[idx]), np.log10(psd.T[idx, sensor]))
                      for sensor in range(psd.shape[0])]
    
    # append a dictionary that holds all the relevant info
    datadict = {'EID': pid}
    for name, fits in [('semilog', semilogfits), ('loglog', loglogfits)]:
        datadict.update(
            {name + 'slopes_individual'    : [fit.slope for fit in fits],
             name + 'intercept_individual' : [fit.intercept for fit in fits],
             name + 'rval_individual'      : [fit.rvalue for fit in fits],
             name + 'slopes_mean'    : np.mean([fit.slope for fit in fits]),
             name + 'intercept_mean' : np.mean([fit.intercept for fit in fits]),
             name + 'rval_mean'      : np.mean([fit.rvalue for fit in fits])}
        )

    alldata.append(datadict)


# ## Load the phenotypic data & combine with data so far

# In[17]:

from data import phenotypes

phenotypes = phenotypes.set_index('EID')

alldf = pd.DataFrame(alldata).set_index('EID').join(phenotypes, how='inner')

plt.scatter(alldf['Age'], alldf['loglogslopes_mean'])
plt.show();
print(scipy.stats.pearsonr(alldf['Age'], alldf['loglogslopes_mean']))

plt.scatter(alldf['Age'], alldf['semilogintercept_mean'])
plt.show();
print(scipy.stats.pearsonr(alldf['Age'], alldf['semilogintercept_mean']))


# In[16]:

plt.scatter(alldf['loglogslopes_mean'], alldf['loglogintercept_mean'])
plt.show();
print(scipy.stats.pearsonr(alldf['loglogslopes_mean'], alldf['loglogintercept_mean']))


# In[ ]:



