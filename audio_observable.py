import pandas as pd
import numpy as np
import wave
from scipy import signal
import pyaudio  
import pyqtgraph as pg
from PyQt5 import QtGui
from PyQt5.QtGui import QDialog
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PyQt5.QtWidgets import QSpinBox, QSlider
from PyQt5.QtCore import pyqtSlot
import sys

from observable import Observable
from observer import Observer

class DisplayObserver(Observer):
    
    """
    stft_length: Length of the shoft-time fourier transform to use
    n_bins: Length of the frequency-domain bins to be used in the frequency plot
    sample_freq: Sampling rate of the audio source in hz
    """
    def __init__(self, stft_length=1024, n_bins=100, sample_freq=44100,
                 logscale=False, decibles=False, freq_range=[0,20000]):
        # Grab inputs
        self.stft_length = stft_length
        self.n_bins = n_bins
        self.sample_freq = sample_freq
        self.logscale = logscale
        self.decibles=decibles
        self.freq_range = freq_range
        
        # Start plot   
        # Set up graph widget
        self.widget = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()
        self.widget.setLayout(self.layout)   
        self.plot = pg.PlotWidget()
        self.plot.setMouseEnabled(False, False)
        self.layout.addWidget(self.plot, 0, 2, 3, 1) # Main freq graph 
        
        # Buttons
        self.logbtn = QPushButton('Toggle logscale')
        self.layout.addWidget(self.logbtn, 0, 0)
        self.logbtn.clicked.connect(self.log_click)
        self.decbtn = QPushButton('Toggle dB')
        self.layout.addWidget(self.decbtn, 1,0)
        self.decbtn.clicked.connect(self.decible_click)
        self.widget.show()
        
        self.plot.setLogMode(logscale, False)
        self.line = self.plot.plot(pen='y')
        
        # Set default options
        if logscale:
            self.plot.setXRange(np.log10(freq_range[0]+1), np.log10(freq_range[1]))
        else:
            self.plot.setXRange(freq_range[0], freq_range[1])
            
        if decibles:
            self.plot.setYRange(0,150)
        else:
            self.plot.setYRange(0, 100000)

    def update(self, *args, **kwargs):
        # Transform data
        input_data = np.fromstring(args[0], dtype=np.int16)
        frequencies,_,data = signal.spectrogram(input_data, fs=self.sample_freq, nfft=self.stft_length*32, nperseg=self.stft_length)
        if data.shape[1] < 2L:
            return
        if self.decibles:
            data = 20*np.log10(1+data)
        data = (data[:,0] + data[:,1])/2
        graph_data = pd.DataFrame()
        graph_data['freq'] = pd.Series(frequencies)
        graph_data['magnitude'] = pd.Series(data)
        graph_data = graph_data[graph_data['freq'] < self.freq_range[1]]
        graph_data = graph_data[graph_data['freq'] > self.freq_range[0]]
        
        # Update plot
        self.line.setData(graph_data['freq'].as_matrix(), graph_data['magnitude'].as_matrix())
        QtGui.QApplication.processEvents()    

    def close(self):
        self.widget.close()
        
    @pyqtSlot()
    
    # Button functions
    def log_click(self):
        self.logscale = not self.logscale
        self.plot.setLogMode(self.logscale, False)
        if self.logscale:
            self.plot.setXRange(np.log10(self.freq_range[0]+1), 
                                np.log10(self.freq_range[1]))
        else:
            self.plot.setXRange(self.freq_range[0], self.freq_range[1])
        
        # Idk why this is necessary here but it is
        if self.decibles:
            self.plot.setYRange(0,150)
        else:
            self.plot.setYRange(0, 10**6)
            
    def decible_click(self):
        self.decibles = not self.decibles
        self.plot.setLogMode(self.logscale, False)
        if self.decibles:
            self.plot.setYRange(0,150)
        else:
            self.plot.setYRange(0, 10**6)
        
        # Idk why this is necessary here but it is
        if self.logscale:
            self.plot.setXRange(np.log10(self.freq_range[0]+1), 
                                np.log10(self.freq_range[1]))
        else:
            self.plot.setXRange(self.freq_range[0], self.freq_range[1])
    
class SoundObserver(Observer):
        def __init__(self, stream):
            self.stream = stream
        
        def update(self, *args, **kwargs):
            self.stream.write(args[0])

# Plot Test
if __name__ == "__main__":
   # Needed because pyQT remains in spyder namespace
    if not QtGui.QApplication.instance():
        app = QtGui.QApplication([])
    else:
        app = QtGui.QApplication.instance() 
    app.exec_()
    
    # Open file
    sound_file = ".\singing_samples\\a_yeah_yeah.wav"
    opera_tenor = wave.open(sound_file, 'rb')
    p = pyaudio.PyAudio()  
    stream = p.open(format = p.get_format_from_width(opera_tenor.getsampwidth()),  
                    channels = opera_tenor.getnchannels(),  
                    rate = opera_tenor.getframerate(),  
                    output = True)  
    read_length = 2048

    # Set up Observer-Listeners
    observable = Observable()
    sound_player = SoundObserver(stream)
    displayer = DisplayObserver(stft_length = read_length, logscale=False,
                                 decibles=True, freq_range=[30,2000])
    observable.register(sound_player)
    observable.register(displayer)
    
    # Play audio and display frequency response
    data = opera_tenor.readframes(read_length)  
    while data:  
        observable.update_observers(data)
        data = opera_tenor.readframes(read_length)  
    
    displayer.close()
    sys.exit(app.exec_())
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
