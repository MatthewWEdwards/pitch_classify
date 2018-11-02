import numpy as np
import yaml
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton
from scipy.signal import spectrogram

from observer import Observer
from audio_singleton import AudioSingleton

class SpectrumWidget(QWidget, Observer):
    logscale = False
    decibels = False
    hann = True
    playing_flag = False
    config = yaml.load(open('config.yaml', 'rb').read())

    def __init__(self, hann=True):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        self.hann = hann
        
        ### Plot ###
        self.plot = pg.PlotWidget()
        self.layout.addWidget(self.plot, 0, 1, 3, 1) # Main freq graph
        self.setLayout(self.layout)
        self.line = self.plot.plot(pen='y')
        self.plot.setMouseEnabled(False, False)
        ### End Plot ###
        
        ### Buttons ###
        self.log_btn = QPushButton('Toggle logscale')
        self.layout.addWidget(self.log_btn, 0, 0)
        self.log_btn.clicked.connect(self.log_click)
        
        self.dec_btn = QPushButton('Toggle dB')
        self.layout.addWidget(self.dec_btn, 1,0)
        self.dec_btn.clicked.connect(self.decibel_click)
        ### End Buttons ###
        
        self.plot.setXRange(self.config['plots']['freq_min'], 
                            self.config['plots']['freq_max'])
        self.plot.setYRange(0, self.config['plots']['y_linear'])
        
        self.plot.setLogMode(False, False)
        self.line = self.plot.plot(pen='y')

        self.audio_singleton = AudioSingleton()
    
    """
    audio_data: file object from the output of a call to wave.read()
    """
    def update(self, *args, **kwargs):
        data = kwargs.get('data', None)
        clear_flag = kwargs.get('clear_flag', False)
        sample_freq = kwargs.get('sample_freq', self.config['sample_frequency'])

        if clear_flag:
            self.clear()

        if data is None:
            return

        self.set_plot(self.audio_singleton.get_audio_data(data), self.audio_singleton.get_sample_rate())

    def clear(self):
        pass

    def set_plot(self, data, sample_freq):
        channel_sum = 0
        if data.ndim > 1:
            for channel in range(data.shape[1]):
                channel_sum = channel_sum + data[:, channel]/data.shape[1]
        freqs, display_data = self.transform(channel_sum, sample_freq)
        freqs = np.array(freqs)
        self.freq_data = freqs[np.where((freqs < self.config['plots']['freq_max']) & (freqs >= self.config['plots']['freq_min']))]
        display_data = display_data[np.where((freqs < self.config['plots']['freq_max']) & (freqs >= self.config['plots']['freq_min']))]
        len_data = len(display_data)/2
        display_data = display_data/(len_data)
        if self.decibels:
            display_data = 20*np.log2(display_data)
        self.display_data = display_data
        self.line.setData(self.freq_data, self.display_data[:,0])
        QtWidgets.QApplication.processEvents() 
        
    def transform(self, data, sample_freq):
        if self.hann:
            data = data * np.hanning(len(data))    
        
        # TODO: Make this configurable
        stft_length = 1024
    
        frequencies,_,data = spectrogram(data*(2**16), fs=sample_freq, nfft=4*stft_length, 
            nperseg=stft_length, scaling='spectrum')
        return (frequencies, data)
        
    """
    Button functions
    """
    def log_click(self):
        self.logscale = not self.logscale
        self.plot.setLogMode(self.logscale, False)
        
        if self.logscale:
            self.plot.setXRange(np.log2(self.config['plots']['freq_min']+1), 
                                np.log2(self.config['plots']['freq_max']+1))
        else:
            self.plot.setXRange(self.config['plots']['freq_min'], self.config['plots']['freq_max'])
        
        if self.decibels:
            self.plot.setYRange(0,self.config['plots']['y_log'])
        else:
            self.plot.setYRange(0, self.config['plots']['y_linear'])
            
    def decibel_click(self):
        self.decibels = not self.decibels
        if self.decibels:
            self.plot.setYRange(0,self.config['plots']['y_log'])
        else:
            self.plot.setYRange(0, self.config['plots']['y_linear'])
    """
    End button functions
    """
