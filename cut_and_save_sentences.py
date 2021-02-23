"""
1)Gets a "beep" sample file -the separator
Gets a file that is full of occasions of this separator
return timepoints in the file that are the end of sentences and time points that are the beginning of sentences

2)Gets sentence beginning and sentence ending and saves the files that contains all sentences

"""

import numpy as np
from os.path import join
import os
from scipy.io import wavfile
from scipy import signal
import matplotlib.pyplot as plt
from matplotlib import use


def turn_num_to_file_format(num):
    num_name = num
    if num < 10:
        num_name = f"00{num}"
    elif num < 100:
        num_name = f"0{num}"
    return str(num_name)


# params
N_FILES_TO_CUT = 7  # THE NUMBER OF WAV FILES IN DIR
FIRST_FILE = 2
SPEAKER = "joey"  # from amazon polly speakers
SFREQ_TO_SAVE = 44100
POD = "parrots"
SEP_FILE = "separator_beep_example_joey.wav"
manual_ignore = {}  # [file, indexes in beep_locs] in case of fake threshold crossing

dir_files = os.listdir()  # files should be in the same dir with scripts STARTING WITH "PODCAST_..."
# %%
for i in range(N_FILES_TO_CUT):
    # load files
    file_path = dir_files[FIRST_FILE + i]
    first_sentence_num = file_path[-11:-8]
    last_sentence_num = file_path[-7:-4]
    n_sentences = int(last_sentence_num) - int(first_sentence_num) + 1
    print(f"Starting to cut from file {file_path}")

    sep_file = wavfile.read(SEP_FILE)
    sep_file_f = sep_file[0]
    sep_file = sep_file[1]  # [int(0.2 * sep_file_f):int(1.45 * sep_file_f)]
    curr_file = wavfile.read(file_path)
    # calc cross correlation and mark times
    cross_cor = np.correlate(curr_file[1], sep_file, mode='same')
    peak_cc = 40  # np.max(cross_cor) * .955  # this might cause missing errors
    # look for threshold crossings in cross_cor which where at 0, 0.5 seconds before the peak
    beep_locs = np.where(cross_cor > peak_cc)[0];  # by threshold
    # beep_locs = beep_locs[(cross_cor[beep_locs-int(0.65*sep_file_f)]<0.01) and
    #                       (cross_cor[beep_locs-int(0.65*sep_file_f)]<0.01)] # remove false alarms of crossing by looking for zero 0.5 secs before
    beep_locs = np.append(beep_locs, 0)
    beep_locs_diff = np.concatenate([np.diff(beep_locs), [0]])
    beep_locs = beep_locs[np.abs(beep_locs_diff) > 1]
    if i in manual_ignore.keys():  # if there is a manual fix
        beep_locs = np.delete(beep_locs, manual_ignore[i])

    sentence_beginnings = np.concatenate([[0], beep_locs[:-1] + int(.95 * sep_file_f)])
    # zero for the first sentence, until the beep before last that marks the beginning of last sentence
    sentence_endings = (beep_locs - int(sep_file[0] / 3))

    # 2)
    for k in range(n_sentences):
        sentence_name = turn_num_to_file_format(int(first_sentence_num) + k)
        sentence_start = sentence_beginnings[k]
        sentence_finish = sentence_endings[k]
        sentence = curr_file[1][sentence_start:sentence_finish]
        sentence = sentence[0:(len(sentence)-int(0.65*sep_file_f))]  # remove last 0.65 seconds of overlap with beep

        sentence_resampled = signal.resample(sentence, int(SFREQ_TO_SAVE * len(sentence) / sep_file_f))
        filename_to_save = f"podcast_{POD}_{SPEAKER}_{sentence_name}.wav"
        print(f"saving {filename_to_save}...")
        wavfile.write(filename_to_save, SFREQ_TO_SAVE, sentence_resampled)
#
# df = pd.DataFrame(data={"col1":dir})
# df.to_csv("./names.csv", sep=',',index=False)