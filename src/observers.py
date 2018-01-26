import pandas as pd
import numpy as np
from scipy.signal import spectrogram

from observer import Observer

class DisplayObserver(Observer):
    
    """
    stft_length: Length of the shoft-time fourier transform to use
    sample_freq: Sampling rate of the audio source in hz
    freq_range: Frequencies to return data for
    hann: If true, multiply the data by a hanning window before taking the fft
    """
    def __init__(self, stft_length=1024, sample_freq=44100,
                 freq_range=[0,20000], hann = False):
        # Grab inputs
        self.stft_length = stft_length
        self.sample_freq = sample_freq
        self.freq_range = freq_range
        self.hann = hann

    def update(self, *args, **kwargs):
        # Transform data
        data = kwargs.get('data', False)
        if not data:
            return
        
        input_data = np.fromstring(data, dtype=np.int16)        
        frequencies, data = self.transform(input_data)
        
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
    
    def transform(self, input_data):
        if self.hann:
            input_data = input_data * np.hanning(len(input_data))    
        
        frequencies,_,data = spectrogram(input_data, fs=self.sample_freq, 
                                nfft=self.stft_length*4, nperseg=self.stft_length,
                                scaling='spectrum')
        return (frequencies, data)
        
        

class SoundObserver(Observer):
        def __init__(self, stream):
            self.stream = stream
        
        def update(self, *args, **kwargs):
            data = kwargs.get('data', False)
            if not data:
                return
            self.stream.write(data)
    
    
    
    
    
    
    
    
    
    
    