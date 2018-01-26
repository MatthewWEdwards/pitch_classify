import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import winsound
from pydub import AudioSegment
import wave
from scipy.signal import stft
from scipy.io import wavfile
from scipy import signal
import thread
import time

matplotlib.use('TkAgg')
#%% Play original file
sound_file = ".\singing_samples\opera_tenor.wav"
opera_tenor = open(sound_file, 'rb')
opera_tenor_samples = opera_tenor.read()
winsound.PlaySound(opera_tenor_samples, winsound.SND_MEMORY)

#%% Play 1 second of audio
new_file = "./recut_files/recut_opera.wav"
opera_tenor_cut = AudioSegment.from_wav(sound_file)

milliseconds = 2000

opear_tenor_cut = opera_tenor_cut[0:milliseconds] # 1 second
opear_tenor_cut.export(new_file, format="wav")
opera_tenor_cut = open(new_file, 'rb')
opera_tenor_samples = opera_tenor_cut.read()
winsound.PlaySound(opera_tenor_samples, winsound.SND_MEMORY)

#%% Plot samples
sample_rate, samples = wavfile.read(new_file)
channel_sum = (samples[:,0] + samples[:,1])/2
frequencies, times, spectrogram = signal.spectrogram(channel_sum, sample_rate)
spectrogram = 20*np.log10(1 + spectrogram) # Convert to dB 
num_frames = int(spectrogram.shape[1])

plt.plot(channel_sum)
plt.title('Raw Input')
plt.xlabel('sample')
plt.ylabel('magnitude')
plt.show()

plt.pcolormesh(times, frequencies, spectrogram)
plt.ylabel('Frequency [Hz]')
plt.xlabel('Time [sec]')
plt.title('Channel Spectrogram')
plt.show()

#%% Freq domain display
freq_plot, ax = plt.subplots()

def update_freq(frame):
    data = spectrogram[:, frame]
    ax = plt.plot(frequencies, data, color='b')
    return ax

downsample = 1
frames = np.array(range(spectrogram.shape[1]))[1::downsample]
spec_animation = animation.FuncAnimation(freq_plot, update_freq, 
                                         frames=frames,
                                         interval=milliseconds/num_frames, 
                                         blit=True)
plt.title('Animiated Frequency')
plt.xlabel('frequency (hz)')
plt.ylabel('Magnitude (dB)')
plt.ylim([0, 100])
plt.show()
    

#%% Define functions for threading
def play_sound(sound_file):    
    opera_tenor_cut = open(sound_file, 'rb')
    opera_tenor_samples = opera_tenor_cut.read()
    winsound.PlaySound(opera_tenor_samples, winsound.SND_MEMORY)

#%% Play song and display frequency spectra simultaneously 

thread.start_new_thread(play_sound, ("./recut_files/recut_opera.wav",))

freq_plot, ax = plt.subplots()
frames = np.array(range(spectrogram.shape[1]))
spec_animation = animation.FuncAnimation(freq_plot, update_freq, 
    frames=frames,interval=milliseconds/num_frames, blit=True)
plt.title('Animiated Frequency')
plt.xlabel('frequency (hz)')
plt.ylabel('Magnitude (dB)')
plt.ylim([0, 100])
plt.show()


