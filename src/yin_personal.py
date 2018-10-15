import numpy as np
import wave
import pyaudio
import pyqtgraph as pg
import yaml
import matplotlib.pyplot as plt
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget

from observable import Observable
from observers import SoundObserver

from noconflict import classmaker

class YinWidget(QWidget, Observable):
    
    signal = QtCore.pyqtSignal(int, bool)
    __metaclass__ = classmaker()
    
    peak_power = 0
    average_power = 0
    power_samples = 0
    current_power = 0        
    power_sensitivity = .1
    # Init Holders
    yin_data = np.array([0])
    num_display_vals = 300 # TODO: make changeable

    def __init__(self):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        # Config Values              
        config = yaml.load(open('../config.yaml', 'rb').read())
        self.read_length = config['read_length']
        self.freq_range = [config['plots']['freq_min'], config['plots']['freq_max']]
        self.sample_freq = config['sample_frequency']
        self.threshold = config['yin']['threshold']
        
        # Plots
        self.yin_plot = pg.PlotWidget()
        self.layout.addWidget(self.yin_plot, 0, 0)
        self.yin_line = self.yin_plot.plot(pen='y')
        self.yin_plot.setMouseEnabled(False, False)
        self.yin_plot.setYRange(0, 500)
        
        # End init
        self.show()
    
    """
    Sound is not played by this function
    """
    def update_trigger(self, data, clear_flag):
        if clear_flag:
            self.signal.emit([], True)
            self.yin_data = np.array([0])
            return
        
        if not data:
            return
        
        data = np.array(data)
        
        ### YIN algorithm ###
        # Differencing function (Step 1-2)
        lag_min = int(np.ceil(self.sample_freq / self.freq_range[1]))
        lag_max = int(np.ceil(self.sample_freq / self.freq_range[0]))
        d = np.zeros(lag_max)
        d_prime = np.zeros(lag_max)
        for lag in range(1, lag_max):
            rolled_data = data[lag:lag + lag_max]
            base_data = data[0:lag_max]
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
            rolled_data = np.array(data[lag:int(np.ceil(lag + lag_max))]).astype('int64')
            base_data = np.array(data[0:lag_max]).astype('int64')
            periodic_power = (.25/window_length)*(np.sum(np.square(rolled_data + base_data)))
            aperiodic_power = (.25/window_length)*(np.sum(np.square(rolled_data - base_data)))
            aperiodic_power_ratio = aperiodic_power / (periodic_power + aperiodic_power)
            if aperiodic_power_ratio < self.threshold:
                period_candiates.update({lag: d_prime[lag]})
        sorted_candidates = sorted(period_candiates.items(), key = lambda candidate_tuple : candidate_tuple[1])
        
        # Steps 5 and 6 not implemented
            
        # Choose between value from step 3 and value from step 4
        if len(period_candiates) == 0: # if no candidates found below threshold
            pitch_d = self.sample_freq/np.argmin(d_prime)
        else:
            pitch_d = self.sample_freq/sorted_candidates[0][0] 
            
        ### End YIN algorithm ###
        #if self.update_power(data) < self.power_sensitivity*self.average_power:
        #    pitch_d = self.yin_data[-1]

        self.signal.emit(pitch_d, False)
        self.yin_data = np.append(self.yin_data, pitch_d)
        
        self.yin_line.setData(range(min(self.yin_data.shape[0], self.num_display_vals)), 
                            self.yin_data[-self.num_display_vals:])

        QtGui.QApplication.processEvents() 

    
    def update_power(self, x):
        power = self.calculate_power(x)
    
        if power > self.peak_power:
            self.peak_power = power
            
        self.power_samples = self.power_samples + 1
        self.average_power = self.average_power + (power / self.power_samples)
        
        print(power)
        print(self.peak_power)
        print(self.average_power)
        print("========================")
        
        return power
    
    def calculate_power(self, x):
        x = x.astype(int)
        return np.dot(x,x)

if __name__ == '__main__':
    #%% Open sound file, prepare arrays
    sound_file = "../singing_samples/a_yeah_yeah.wav" # 'a' note
    audio_data = wave.open(sound_file, 'rb')
    
    p = pyaudio.PyAudio()  
    for i in range(0, p.get_device_count()):
            print("name: " + p.get_device_info_by_index(i)["name"])
            print("index: " + p.get_device_info_by_index(i)["index"])
            print("\n")
    #stream = p.open(format = p.get_format_from_width(audio_data.getsampwidth()),  
    #                channels = audio_data.getnchannels(),  
    #                rate = audio_data.getframerate(),  
    #                output_device_index = 1,
    #                output = True)     
            
    read_length = 2**11
    observable = Observable()
    #sound_player = SoundObserver(stream)
    #observable.register(sound_player)
        
    data = audio_data.readframes(read_length)  
    
    pitch_array = np.ndarray([])
    d_array = np.ndarray([])
    
    #%% Difference function
    def difference_val(data, read_length):
        lag_max = int(read_length/2)
        d = np.zeros(lag_max)
        for lag in range(0, lag_max):
            rolled_data = data[lag:int(np.ceil(lag + lag_max))]
            base_data = data[0:lag_max]
            if len(rolled_data) != len(base_data):
                break 
            d[lag] = np.sum(np.abs(rolled_data - base_data))
        return d
    
    #%% Find pitch for chunks of data
    while data:  
        #observable.update_observers(data)
        data = np.fromstring(data, dtype=np.int16)
        if data.shape[0] < read_length*2:
            data = audio_data.readframes(read_length)
            continue
        
        # autocorrelation with differencing (step 3)
        d = difference_val(data, read_length)
        d = d / ((1/float(read_length/2))*np.sum(d))
    
        d[:50] = np.inf
        pitch_d = 44100/np.argmin(d)
        print("difference: " + str(pitch_d))
    
        d_array = np.append(d_array, pitch_d)
        data = audio_data.readframes(read_length)
    
    
    #%% Show results
    plt.plot(d_array)
    plt.show()
    
    
    
