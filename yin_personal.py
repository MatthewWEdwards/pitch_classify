import matplotlib.pyplot as plt
from scipy.fftpack import fft
from scipy.io import wavfile
import numpy as np
import pyaudio
import wave

from observers import SoundObserver
from observable import Observable

#%% Open sound file, prepare arrays
sound_file = ".\\singing_samples\\a_yeah_yeah.wav"
audio_data = wave.open(sound_file, 'rb')

p = pyaudio.PyAudio()  
stream = p.open(format = p.get_format_from_width(audio_data.getsampwidth()),  
                channels = audio_data.getnchannels(),  
                rate = audio_data.getframerate(),  
                output = True)     
        
read_length = 2**10
observable = Observable()
sound_player = SoundObserver(stream)
observable.register(sound_player)
    
data = audio_data.readframes(read_length)  

pitch_array = np.ndarray([])
d_array = np.ndarray([])

#%% Difference function
def difference_val(data, read_length):
    lag_max = read_length/2
    d = np.zeros(lag_max)
    for lag in range(0, lag_max):
        rolled_data = data[lag:int(np.ceil(lag + lag_max))]
        base_data = data[0:read_length/2]
        if len(rolled_data) != len(base_data):
            break 
        d[lag] = np.sum(np.abs(rolled_data - base_data))
    return d

#%% Find pitch for chunks of data
while data:  
    observable.update_observers(data)
    data = np.fromstring(data, dtype=np.int16)
    if data.shape[0] < read_length*2:
        data = audio_data.readframes(read_length)
        continue
    
    # autocorrelation with differencing (step 3)
    d = difference_val(data, read_length)
    d = d / ((1/float(read_length/2))*np.sum(d))

    d[:50] = np.inf
    pitch_d = 44100/np.argmin(d)
    print "difference: " + str(pitch_d)    

    d_array = np.append(d_array, pitch_d)
    data = audio_data.readframes(read_length)


#%% Show results
plt.plot(d_array)
plt.show()













