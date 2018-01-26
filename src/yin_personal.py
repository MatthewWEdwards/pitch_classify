import numpy as np
import wave
import pyaudio
import pyqtgraph as pg
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget

from observable import Observable
from observers import SoundObserver

from noconflict import classmaker

class YinWidget(QWidget):
    __metaclass__ = classmaker()

    def __init__(self):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        # Defaults              
        self.read_length = 2**11
        self.freq_range = [30, 500]
        
        # Plots
        self.yin_plot = pg.PlotWidget()
        self.layout.addWidget(self.yin_plot, 0, 0)
        self.yin_line = self.yin_plot.plot(pen='y')
        self.yin_plot.setMouseEnabled(False, False)
        self.yin_plot.setYRange(0, 500)
        
        # Init Holders
        self.yin_data = np.array([0])
        self.num_display_vals = 300 # TODO: make changeable
        
        # End init
        self.show()
    
    """
    Sound is not played by this function
    """
    def update_trigger(self, data, clear_flag):
        if clear_flag:
            self.pitch_data = np.array([0])
            return
        
        if not data:
            return
        
        data = np.array(data)
        
        ## YIN algorithm
        
        # autocorrelation with differencing (step 3)
        lag_max = self.read_length/2
        d = np.zeros(lag_max)
        for lag in range(0, lag_max):
            rolled_data = data[lag:int(np.ceil(lag + lag_max))]
            base_data = data[0:self.read_length/2]
            if len(rolled_data) != len(base_data):
                break 
            d[lag] = np.sum(np.abs(rolled_data - base_data))
        d = d / ((1/float(self.read_length/2))*np.sum(d))
    
        # Find dip candidates (step 4)
        period_candiates = {}
        threshold = 0.05
        window_length = self.read_length/2
        lag_max = self.read_length/2
        for lag in range(50, 800):        
            rolled_data = np.array(data[lag:int(np.ceil(lag + lag_max))]).astype('int64')
            base_data = np.array(data[0:self.read_length/2]).astype('int64')    
            periodic_power = (.25/window_length)*(np.sum(np.square(rolled_data + base_data)))
            aperiodic_power = (.25/window_length)*(np.sum(np.square(rolled_data - base_data)))
            aperiodic_power_ratio = aperiodic_power / (periodic_power + aperiodic_power)
            if aperiodic_power_ratio < threshold:
                period_candiates.update({lag: aperiodic_power_ratio})
                
        # Choose between value from step 3 and value from step 4
        if len(period_candiates) == 0: # if no candidates found
            d[:50] = np.inf
            pitch_d = 44100/np.argmin(d)
        else:
            sorted_candidates = sorted(period_candiates.iteritems(), key=lambda(k,v): (v,k))
            pitch_d = 44100/sorted_candidates[0][0]
            
        ## End YIN algorithm
                        
        # Update plot
        calc_vol = np.sum(np.abs(data))
        if calc_vol < len(data)*1000:
            self.yin_data = np.append(self.yin_data, self.yin_data[-1])
        else:
            self.yin_data = np.append(self.yin_data, pitch_d)
        self.yin_line.setData(range(min(self.yin_data.shape[0], self.num_display_vals)), 
                            self.yin_data[-self.num_display_vals:])

        QtGui.QApplication.processEvents() 


if __name__ == '__main__':
    #%% Open sound file, prepare arrays
    sound_file = ".\\singing_samples\\rehearsal_music.wav" # 'a' note
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
        print "difference: " + str(pitch_d)    
    
        d_array = np.append(d_array, pitch_d)
        data = audio_data.readframes(read_length)
    
    
    #%% Show results
    plt.plot(d_array)
    plt.show()
    
    
    
    
    
    
    
    
    
    
    
    
    
