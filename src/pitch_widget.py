import numpy as np
import wave
import pyqtgraph as pg
import yaml
import matplotlib.pyplot as plt
from PyQt5 import QtGui, QtCore
from PyQt5.QtWidgets import QWidget, QComboBox
import threading
import queue

from observer import Observer
from observable import Observable

from noconflict import classmaker
from audio_singleton import AudioSingleton
from PitchDetectionStrategy import PitchDetectionStrategy
from YinStrategy import YinStrategy
from CepstrumStrategy import CepstrumStrategy

class PitchWidget(QWidget, Observer, Observable):
    __metaclass__ = classmaker()
    
    peak_power = 0
    average_power = 0
    power_samples = 0
    power_sensitivity = .1
    pitch_data = np.array([0])

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
        self.threshold = self.config['yin']['threshold'] # TODO: Move this to Yin strategy
        
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
        sample_freq = kwargs.get('sample_freq', 44100)

        if clear_flag:
            self.pitch_data = np.array([0])
        
        if data is None:
            return

        pitch_d = self.pitch_strategies[self.comboBox.currentIndex()].detect_pitch(
            data = self.audio_singleton.get_audio_data(data), sample_freq = self.audio_singleton.get_sample_rate())
        
        # If power too low
        if self.update_power(self.audio_singleton.get_audio_data(data)) < self.power_sensitivity*self.average_power:
            if len(self.pitch_data) > 0:
                pitch_d = self.pitch_data[-1]

        self.pitch_data = np.append(self.pitch_data, pitch_d)
        self.pitch_line.setData(range(min(self.pitch_data.shape[0], self.config['pitch']['num_display'])), 
        self.pitch_data[-self.config['pitch']['num_display']:])

        if len(self.observers) > 0:
            self.update_observers(freq = pitch_d)

    def update_power(self, x):
        power = self.calculate_power(x)
    
        if power > self.peak_power:
            self.peak_power = power
            
        self.power_samples = self.power_samples + 1
        self.average_power = self.average_power + (power / self.power_samples)

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

