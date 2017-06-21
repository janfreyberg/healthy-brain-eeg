from pathlib import Path
import os
import shutil
import sys
import platform

# where the compressed data is stored
datadir = Path('D:\\') / 'cmi-hbn'
# where 7zip is stored
if platform.system() == 'Windows':
    zipcommand = '7z'

# find the compressed Files
tarfiles = datadir.glob('*.tar.gz')

# extraction
for tarfile in tarfiles:
    # only proceed if there isn't a folder already:
    subjectid = tarfile.name[:-7]
    # extract the preproc eeg data
    if not os.path.isdir(datadir / subjectid):
        # build the command to extract

        command = (
            # extract the tar
            zipcommand + ' x "' + str(tarfile) + '" -so | ' +
            # extract the files
            zipcommand + ' x -aoa -si -ttar -o' + '"' + str(datadir) + '"'
        )
        # run the command
        print(command)
        os.system(command)

        # remove any unwanted files
        try:
            shutil.rmtree(datadir / subjectid / 'EEG' / 'raw')
        except:
            pass
        try:
            shutil.rmtree(datadir / subjectid / 'EEG' /
                          'preprocessed' / 'mat_format')
        except:
            pass
        try:
            shutil.rmtree(datadir / subjectid / 'Eyetracking' / 'idf')
        except:
            try:
                shutil.rmtree(datadir / subjectid /
                              'Eyetracking' / 'idf_format')
            except:
                pass

        # remove the TAR file itself
        os.remove(tarfile)
