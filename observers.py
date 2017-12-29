import pandas as pd
import numpy as np
from scipy import signal

from observer import Observer

class DisplayObserver(Observer):
    
    """
    stft_length: Length of the shoft-time fourier transform to use
    n_bins: Length of the frequency-domain bins to be used in the frequency plot
    sample_freq: Sampling rate of the audio source in hz
    """
    def __init__(self, stft_length=1024, sample_freq=44100,
                 freq_range=[0,20000]):
        # Grab inputs
        self.stft_length = stft_length
        self.sample_freq = sample_freq
        self.freq_range = freq_range

    def update(self, *args, **kwargs):
        # Transform data
        input_data = np.fromstring(args[0], dtype=np.int16)
        frequencies,_,data = signal.spectrogram(input_data, fs=self.sample_freq, nfft=self.stft_length*32, nperseg=self.stft_length)
        
        if data.shape[0] < 1:
            return
        
        channel_sum = 0
        for channel in range(data.shape[1]):
            channel_sum = channel_sum + data[:,channel]/data.shape[1]
            
        graph_data = pd.DataFrame()
        graph_data['freq'] = pd.Series(frequencies)
        graph_data['magnitude'] = pd.Series(channel_sum)
        graph_data = graph_data[graph_data['freq'] < self.freq_range[1]]
        graph_data = graph_data[graph_data['freq'] > self.freq_range[0]]
        self.graph_data = graph_data

class SoundObserver(Observer):
        def __init__(self, stream):
            self.stream = stream
        
        def update(self, *args, **kwargs):
            self.stream.write(args[0])
    
    
    
    
    
    
    
    
    
    
    
