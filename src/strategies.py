import numpy as np
from scipy.fftpack import fft, ifft
import matplotlib.pyplot as plot

class PitchDetectionStrategy:

    def detect_pitch(self, *args, **kwargs):
        pass

class YinStrategy(PitchDetectionStrategy):
    
    def detect_pitch(self, *args, **kwargs):
        data = kwargs.get('data', [0])
        threshold = kwargs.get('threshold', 0.05) # TODO: Move to config
        sample_freq = kwargs.get('sample_freq', 44100)
        freq_range = kwargs.get('freq_range', [50, 500])

        # Differencing function (Step 1-2)
        channel_sum = 0
        if data.ndim > 1:
            for channel in range(data.shape[1]):
                channel_sum += data[:, channel]
        lag_min = int(np.ceil(sample_freq / freq_range[1]))
        lag_max = int(np.ceil(sample_freq / freq_range[0]))
        d = np.zeros(lag_max)
        d_prime = np.zeros(lag_max)
        for lag in range(1, lag_max):
            rolled_data = channel_sum[lag:lag + lag_max]
            base_data = channel_sum[0:lag_max]
            d[lag] = np.sum(np.square(rolled_data - base_data))
            
        # Normalization (Step 3)
        d_prime[0] = 1
        for lag in range(1,len(d)):
            d_prime[lag] = d[lag] / ((1/lag)*np.sum(d[0:lag+1]))
        d_prime[:lag_min] = np.inf # Invalidate frequencies outside our range
        d_prime[lag_max:] = np.inf # Invalidate frequencies outside our range

        # Find dip candidates, select minimum of d_prime (step 4)
        period_candiates = {}
        window_length = lag_max
        for lag in range(lag_min, lag_max):
            rolled_data = np.array(channel_sum[lag:int(np.ceil(lag + lag_max))]).astype('int64')
            base_data = np.array(channel_sum[0:lag_max]).astype('int64')
            periodic_power = (.25/window_length)*(np.sum(np.square(rolled_data + base_data)))
            aperiodic_power = (.25/window_length)*(np.sum(np.square(rolled_data - base_data)))
            aperiodic_power_ratio = aperiodic_power / (periodic_power + aperiodic_power)
            if aperiodic_power_ratio < threshold:
                period_candiates.update({lag: d_prime[lag]})
        sorted_candidates = sorted(period_candiates.items(), key = lambda candidate_tuple : candidate_tuple[1])
        
        # Steps 5 and 6 not implemented
            
        # Choose between value from step 3 and value from step 4
        if len(period_candiates) == 0: # if no candidates found below threshold
            pitch_d = sample_freq/np.argmin(d_prime)
        else:
            pitch_d = sample_freq/sorted_candidates[0][0] 
    
        return pitch_d

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
        
