import yaml
import collections

import numpy as np
import matplotlib.pyplot as plt

import pyqtgraph as pg
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QComboBox

from observer import Observer
from observable import Observable

from noconflict import classmaker
from audio_singleton import AudioSingleton
from PitchDetectionStrategy import PitchDetectionStrategy
from YinStrategy import YinStrategy
from CepstrumStrategy import CepstrumStrategy

#TODO: Refactor power functions into a separate class
class PitchWidget(QWidget, Observer, Observable):
    __metaclass__ = classmaker()
    
    power_sensitivity = .1
    peak_power = 0
    power_samples = 0
    pitch_data = np.array([0])
    num_display = 300
    power_window = collections.deque(maxlen = 75) # TODO: Config

    def __init__(self, sample_freq=None, pitch_strategies=None, note_widget=None):
        super(QWidget, self).__init__()
        super(Observer, self).__init__()

        if pitch_strategies is None:
            self.pitch_strategies = [CepstrumStrategy(), YinStrategy()]

        if not note_widget is None:
            self.register(note_widget)
        
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        # Config Values              
        self.config = yaml.load(open('config.yaml', 'rb').read())
        self.read_length = self.config['read_length']
        self.freq_range = [self.config['plots']['freq_min'], self.config['plots']['freq_max']]
        if sample_freq is None:
            self.sample_freq = self.config['sample_frequency']
        self.num_display = self.config['pitch']['num_display']
        self.power_sensitivity = self.config['pitch']['power_sensitivity']
        
        # Plots
        self.pitch_plot = pg.PlotWidget()
        self.layout.addWidget(self.pitch_plot, 1, 0)
        self.pitch_line = self.pitch_plot.plot(pen='y')
        self.pitch_plot.setMouseEnabled(False, False)
        self.pitch_plot.setYRange(0, 500)

        self.comboBox = QComboBox()
        self.comboBox.addItem("Cepstrum")
        self.comboBox.addItem("Yin")
        self.layout.addWidget(self.comboBox, 0, 0)
    
        # Data holder
        self.audio_singleton = AudioSingleton()

        # End init
        self.show()
    
    def update(self, *args, **kwargs):
        data = kwargs.get('data', None)
        clear_flag = kwargs.get('clear_flag', False)
        if clear_flag:
            self.pitch_data = np.array([0])
        if data is None:
            return

        data_array = self.audio_singleton.get_audio_data(data)
        sample_freq = self.audio_singleton.get_sample_rate()
        pitch_strategy = self.pitch_strategies[self.comboBox.currentIndex()]
        pitch_d = pitch_strategy.detect_pitch(data = data_array, sample_freq = sample_freq)
        
        # If power too low
        power = self.update_power(data_array)
        print(power)
        print(self.power_floor())
        if power < self.power_floor():
            if len(self.pitch_data) > 0:
                pitch_d = self.pitch_data[-1]
        self.pitch_data = np.append(self.pitch_data, pitch_d)
        self.pitch_line.setData(range(min(self.pitch_data.shape[0], self.num_display)), 
        self.pitch_data[-self.num_display:])

        if len(self.observers) > 0:
            self.update_observers(freq = pitch_d)

    def update_power(self, x):
        power = self.calculate_power(x)
        if power > self.peak_power:
            self.peak_power = power
        self.power_window.append(power)
        self.power_samples = len(self.power_window)
        return power

    def power_floor(self):
        return (sum(self.power_window)/len(self.power_window))*self.power_sensitivity
    
    def calculate_power(self, x):
        # Assume x is at most Nx2
        #x = x.astype(int)
        power = 0
        if x.ndim < 2:
            power = np.dot(x,x)
        else:
            for col in range(x.shape[1]):
                power += np.dot(x[:, col], x[:, col])
        return power

