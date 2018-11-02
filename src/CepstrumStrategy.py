import numpy as np
from scipy.fftpack import fft, ifft

from PitchDetectionStrategy import PitchDetectionStrategy

class CepstrumStrategy(PitchDetectionStrategy):

    def detect_pitch(self, *args, **kwargs):
        data = kwargs.get('data', [0])
        threshold = kwargs.get('threshold', 0.05)
        sample_freq = kwargs.get('sample_freq', 44100)
        freq_range = kwargs.get('freq_range', [50, 500])

        channel_sum = 0
        if data.ndim > 1:
            for channel in range(data.ndim):
                channel_sum += data[:, channel]
        else:
            channel_sum = data
            
        hann_data = np.hanning(len(channel_sum))
        cepstrum_data = np.absolute(ifft(np.log2(1+np.absolute(fft(channel_sum*hann_data)))**2))**2


        cepstrum_data = cepstrum_data[:int(len(cepstrum_data)/2)] 
        min_index = int(np.ceil(sample_freq / freq_range[1]))
        cepstrum_data[:min_index] = 0 # assume freq < freq_range[1]

        return sample_freq/np.argmax(cepstrum_data)
        
