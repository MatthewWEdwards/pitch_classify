import numpy as np
import wave
import pyqtgraph as pg
import yaml
import matplotlib.pyplot as plt
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget
import threading
import queue

from observer import Observer

from noconflict import classmaker

class YinWidget(QWidget, Observer):
    __metaclass__ = classmaker()
    
    peak_power = 0
    average_power = 0
    power_samples = 0
    current_power = 0        
    power_sensitivity = .1
    # Init Holders
    yin_data = np.array([0])
    num_display_vals = 300 # TODO: make changeable

    def __init__(self, sample_freq=None):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        # Config Values              
        config = yaml.load(open('../config.yaml', 'rb').read())
        self.read_length = config['read_length']
        self.freq_range = [config['plots']['freq_min'], config['plots']['freq_max']]
        if sample_freq is None:
            self.sample_freq = config['sample_frequency']
        self.threshold = config['yin']['threshold']
        
        # Plots
        self.yin_plot = pg.PlotWidget()
        self.layout.addWidget(self.yin_plot, 0, 0)
        self.yin_line = self.yin_plot.plot(pen='y')
        self.yin_plot.setMouseEnabled(False, False)
        self.yin_plot.setYRange(0, 500)

        # Threading
        self.thread_queue = queue.Queue()
        yin_thread = threading.Thread(target = self.run)
        yin_thread.start()
        
        # End init
        self.show()
    
    """
    Sound is not played by this function
    """
    def update(self, *args, **kwargs):
        data = kwargs.get('data', None)
        clear_flag = kwargs.get('clear_flag', False)
        sample_freq = kwargs.get('sample_freq', 44100)

        if clear_flag:
            self.yin_data = np.array([0])
        
        if data is None:
            return

        self.thread_queue.put(threading.Thread(target = self.yin, args=(data, sample_freq)))

    
    def yin(self, data, sample_freq):
        ### YIN algorithm ###
        # Differencing function (Step 1-2)
        channel_sum = 0
        if data.ndim > 1:
            for channel in range(data.shape[1]):
                channel_sum += data[:, channel]
        lag_min = int(np.ceil(sample_freq / self.freq_range[1]))
        lag_max = int(np.ceil(sample_freq / self.freq_range[0]))
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
            if aperiodic_power_ratio < self.threshold:
                period_candiates.update({lag: d_prime[lag]})
        sorted_candidates = sorted(period_candiates.items(), key = lambda candidate_tuple : candidate_tuple[1])
        
        # Steps 5 and 6 not implemented
            
        # Choose between value from step 3 and value from step 4
        if len(period_candiates) == 0: # if no candidates found below threshold
            pitch_d = self.sample_freq/np.argmin(d_prime)
        else:
            pitch_d = self.sample_freq/sorted_candidates[0][0] 

        # If power too low
        if self.update_power(data) < self.power_sensitivity*self.average_power:
            if len(self.yin_data) > 0:
                pitch_d = self.yin_data[-1]

        self.yin_data = np.append(self.yin_data, pitch_d)
        self.yin_line.setData(range(min(self.yin_data.shape[0], self.num_display_vals)), 
                            self.yin_data[-self.num_display_vals:])


        return pitch_d
    
    def update_power(self, x):
        power = self.calculate_power(x)
    
        if power > self.peak_power:
            self.peak_power = power
            
        self.power_samples = self.power_samples + 1
        self.average_power = self.average_power + (power / self.power_samples)
        
        #print(power)
        #print(self.peak_power)
        #print(self.average_power)
        #print("========================")
        
        return power
    
    def calculate_power(self, x):
        # Assume x is at most Nx2
        x = x.astype(int)
        power = 0
        if x.ndim < 2:
            power = np.dot(x,x)
        else:
            for col in range(x.shape[1]):
                power += np.dot(x[:, col], x[:, col])
        return power

    def run(self):
        while True:
            while self.thread_queue.empty():
                pass
            thread = self.thread_queue.get()
            thread.start()
            thread.join()
            QtGui.QApplication.processEvents() 

