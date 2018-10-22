import numpy as np
import wave
import yaml
import pyqtgraph as pg
import time
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog
from PyQt5.QtWidgets import QLineEdit
from scipy.signal import spectrogram
import sys
import threading
import queue

from observer import Observer
from observers import DisplayObserver, SoundObserver

class SpectrumWidget(QWidget, Observer):
    
    signal = QtCore.pyqtSignal(list, bool, int)
    playing_flag = False
    
    config = yaml.load(open('../config.yaml', 'rb').read())
    logscale = False
    decibles = False
    freq_range = [config['plots']['freq_min'], config['plots']['freq_max']]
    file_name = ""
    read_length = config['read_length']
    play_audio_flag = False
    quit_flag = False
    sample_rate = 44100
    hann = True

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
        self.logbtn = QPushButton('Toggle logscale')
        self.layout.addWidget(self.logbtn, 0, 0)
        self.logbtn.clicked.connect(self.log_click)
        
        self.dec_btn = QPushButton('Toggle dB')
        self.layout.addWidget(self.dec_btn, 1,0)
        self.dec_btn.clicked.connect(self.decible_click)
        ### End Buttons ###

        # Threading
        self.thread_queue = queue.Queue()
        spec_thread = threading.Thread(target = self.run)
        spec_thread.start()
        
        self.plot.setXRange(self.freq_range[0], self.freq_range[1])
        self.plot.setYRange(0, 10**6)
        
        self.plot.setLogMode(False, False)
        self.line = self.plot.plot(pen='y')
    
    """
    audio_data: file object from the output of a call to wave.read()
    TODO: audio_data only accepts .wav files. Make a wrapper class that can
          accept multiple file types.
    """
    def update(self, *args, **kwargs):
        data = kwargs.get('data', None)
        clear_flag = kwargs.get('clear_flag', False)
        sample_freq = kwargs.get('sample_freq', 44100)

        if clear_flag:
            self.clear()

        if data is None:
            return
        
        self.thread_queue.put(threading.Thread(target = self.set_plot, args=(data, sample_freq)))

    def clear(self):
        pass 

    def set_plot(self, data, sample_freq):
        channel_sum = 0
        if data.ndim > 1:
            for channel in range(data.shape[1]):
                channel_sum = channel_sum + data[:, channel]/data.shape[1]
        freqs, display_data = self.transform(channel_sum, sample_freq)
        freqs = np.array(freqs)
        self.freq_data = freqs[np.where((freqs < self.freq_range[1]) & (freqs >= self.freq_range[0]))]
        display_data = display_data[np.where((freqs < self.freq_range[1]) & (freqs >= self.freq_range[0]))]
        len_data = len(display_data)/2
        if self.decibles:
            display_data = 20*np.log2(display_data / len_data)
        self.display_data = display_data
        self.line.setData(self.freq_data, self.display_data[:,0])
        
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
            self.plot.setXRange(np.log2(self.freq_range[0]+1), 
                                np.log2(self.freq_range[1]+1))
        else:
            self.plot.setXRange(self.freq_range[0], self.freq_range[1])
        
        if self.decibles:
            self.plot.setYRange(0,500)
        else:
            self.plot.setYRange(0, 10**6)
            
    def decible_click(self):
        self.decibles = not self.decibles
        if self.decibles:
            self.plot.setYRange(0,500) # TODO: make this actually based on data
        else:
            self.plot.setYRange(0, 10**6)
    """
    End button functions
    """
    
    def run(self):
        while True:
            while self.thread_queue.empty():
                pass
            thread = self.thread_queue.get()
            thread.start()
            thread.join()
        
#XXX Deprecated main method, won't work.
if __name__ == "__main__":
   # Needed because pyQT remains in spyder namespace
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        
    s_w = SpectrumWidget()
    s_w.show()
    while True:
        QtGui.QApplication.processEvents()
    s_w.close()

    sys.exit(app.exec_())
        
