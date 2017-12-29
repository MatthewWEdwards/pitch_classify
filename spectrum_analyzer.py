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
from observer import Observer
from audio_observable import DisplayObserver, sound_observer

class WidgetObserver(QWidget, Observer):
     pass

class SpectrumWidget(QWidget, Observer):
    __metaclass__ = WidgetObserver
    
    """
    display_observer: a DisplayObserver object
    """
    def __init__(self, DisplayObserver):
        self.setLayout(QtGui.QGridLayout())
        self.layout = QtGui.QGridLayout()
        self.widget.setLayout(self.layout)
        
        self.plot = pg.PlotWidget()
        self.layout.addWidget(self.plot, 0, 1, 3, 1) # Main freq graph
        
        self.logbtn = QPushButton('Toggle logscale')
        self.layout.addWidget(self.logbtn, 0, 0)
        self.logbtn.clicked.connect(self.log_click)
        self.widget.show()
        
        self.plot.setLogMode(DisplayObserver.logscale, False)
        self.line = self.plot.plot(pen='y')
        
        if DisplayObserver.logscale:
            self.plot.setXRange(np.log10(DisplayObserver.freq_range[0]+1), np.log10(DisplayObserver.freq_range[1]))
        else:
            self.plot.setXRange(DisplayObserver.freq_range[0], DisplayObserver.freq_range[1])
        if DisplayObserver.decibles:
            self.plot.setYRange(0,150)
        else:
            self.plot.setYRange(0, 100000)
    
    def initUI(self):
        pass
   
    def update(self, *args, **kwargs):
        graph_data = args[0]
        
        # Update plot
        self.line.setData(graph_data['freq'].as_matrix(), graph_data['magnitude'].as_matrix())
        QtGui.QApplication.processEvents()    
        
if __name__ == "__main__":
    app = QApplication(sys.argv)    
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
    sound_player = sound_observer(stream)
    displayer = DisplayObserver(stft_length = read_length, logscale=False,
                                 decibles=True, freq_range=[30,2000])
    observable.register(sound_player)
    observable.register(displayer)
    
    s_w = SpectrumWidget(displayer)
    
    # Play audio and display frequency response
    data = opera_tenor.readframes(read_length)  
    while data:  
        observable.update_observers(data)
        data = opera_tenor.readframes(read_length)  
    
    sys.exit(app.exec_())
        