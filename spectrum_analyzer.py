import pandas as pd
import numpy as np
import wave
from scipy import signal
import pyaudio  
import pyqtgraph as pg
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PyQt5.QtCore import pyqtSlot
import sys

from observable import Observable
from audio_observable import DisplayObserver, SoundObserver


class SpectrumWidget(QWidget):
    

    def __init__(self):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        
        # Plot
        self.plot = pg.PlotWidget()
        self.layout.addWidget(self.plot, 0, 1, 3, 1) # Main freq graph
        self.setLayout(self.layout)
        self.line = self.plot.plot(pen='y')
        self.plot.setMouseEnabled(False, False)
        
        # Buttons
        self.logbtn = QPushButton('Toggle logscale')
        self.layout.addWidget(self.logbtn, 0, 0)
        self.logbtn.clicked.connect(self.log_click)
        self.decbtn = QPushButton('Toggle dB')
        self.layout.addWidget(self.decbtn, 1,0)
        self.decbtn.clicked.connect(self.decible_click)
        self.logscale = False
        self.decibles = False
        self.freq_range = [30, 2000]
        
        self.plot.setLogMode(False, False)
        self.line = self.plot.plot(pen='y')
        
        self.show()
    
    """
    Loads an audio file. Generates SoundObserver and DisplayObservers to handle
    the data.
    
    Only works for .wav files
    """
    def load_audio(self):
        # Open file
        sound_file = ".\singing_samples\\a_yeah_yeah.wav"
        audio_data = wave.open(sound_file, 'rb')
        p = pyaudio.PyAudio()  
        stream = p.open(format = p.get_format_from_width(audio_data.getsampwidth()),  
                        channels = audio_data.getnchannels(),  
                        rate = audio_data.getframerate(),  
                        output = True)  
        read_length = 2048 # TODO: Make customizable
    
        # Set up Observer-Listeners
        observable = Observable()
        sound_player = SoundObserver(stream)
        #TODO: Make customizable
        displayer = DisplayObserver(stft_length = read_length, freq_range=[30,2000])
        observable.register(sound_player)
        observable.register(displayer)
        
        if self.logscale:
            self.plot.setXRange(np.log10(displayer.freq_range[0]+1), np.log10(displayer.freq_range[1]))
        else:
            self.plot.setXRange(displayer.freq_range[0], displayer.freq_range[1])
      
        if self.decibles:
            self.plot.setYRange(0,150)
        else:
            self.plot.setYRange(0, 100000)


        # Play audio and display frequency response
        data = audio_data.readframes(read_length)  
        while data:  
            data = audio_data.readframes(read_length)  
            observable.update_observers(data)
            disp_data = displayer.graph_data
            # Difference here done for efficiency reasons (RE: Pandas)
            if self.decibles:
                self.line.setData(disp_data['freq'].as_matrix(), 20*np.log10(1+disp_data['magnitude']).as_matrix())
            else:
                self.line.setData(disp_data['freq'].as_matrix(), disp_data['magnitude'].as_matrix())
            QtGui.QApplication.processEvents() 
            
        
    # Button functions
    def log_click(self, ):
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
    

        
if __name__ == "__main__":
   # Needed because pyQT remains in spyder namespace
    if not QtGui.QApplication.instance():
        app = QtGui.QApplication([])
    else:
        app = QtGui.QApplication.instance() 
    app.exec_()
    s_w = SpectrumWidget()
    s_w.load_audio()
    s_w.close()

    sys.exit(app.exec_())
        
