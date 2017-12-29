import pandas as pd
import numpy as np
import matplotlib.pyplot as plot
from scipy.signal import stft


#%% Read pitch and melody samples
pitch_cols = pd.read_csv(".\MedleyDB_sample\Annotations\Pitch_Annotations\Phoenix_ScotchMorris_STEM_02.csv", 
                         nrows=1).columns
pitch_sample = pd.read_csv(".\MedleyDB_sample\Annotations\Pitch_Annotations\Phoenix_ScotchMorris_STEM_02.csv", 
                           usecols=pitch_cols)
pitch_sample.columns = ["seconds", "frequency"]


melody_cols = pd.read_csv(".\MedleyDB_sample\Annotations\Melody_Annotations\MELODY3\Phoenix_ScotchMorris_MELODY3.csv", 
                         nrows=1).columns
melody_sample = pd.read_csv(".\MedleyDB_sample\Annotations\Melody_Annotations\MELODY3\Phoenix_ScotchMorris_MELODY3.csv", 
                          usecols=melody_cols)
melody_sample.columns= ["seconds", "f0", "f1"]
                    


#%% Display pitch
plot.scatter(pitch_sample["seconds"], pitch_sample["frequency"])
plot.title('Pitch Sample')
plot.xlabel('time (seconds)')
plot.ylabel('frequency')
plot.show()

#%% Display melody
plot.scatter(melody_sample["seconds"], melody_sample["f0"], color='r')
plot.hold()
plot.scatter(melody_sample["seconds"], melody_sample["f1"], color='b')
plot.xlabel('time (seconds)')
plot.ylabel('frequency')
plot.show()