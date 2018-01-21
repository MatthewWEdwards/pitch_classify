import numpy as np
from scipy.fftpack import fft, ifft
import wave
import pyaudio
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget
import sys

from observable import Observable
from observer import Observer
from observers import SoundObserver

from noconflict import classmaker


class CepstrumWidget(QWidget):
    __metaclass__ = classmaker()
    
    def __init__(self):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        # Defaults              
        self.read_length = 2**11
        self.freq_range = [30, 2000]
        
        # Plots
        self.cepstrum_plot = pg.PlotWidget()
        self.layout.addWidget(self.cepstrum_plot, 0, 0)
        self.cepstrum_line = self.cepstrum_plot.plot(pen='y')
        self.cepstrum_plot.setMouseEnabled(False, False)
        self.cepstrum_plot.setXRange(0, self.read_length)
        self.cepstrum_plot.setYRange(0, 100)
        
        self.pitch_plot = pg.PlotWidget()
        self.layout.addWidget(self.pitch_plot, 0, 1)
        self.pitch_line = self.pitch_plot.plot(pen='y')
        self.pitch_plot.setMouseEnabled(False, False)
        self.pitch_plot.setYRange(0, 500)
        
        # Init Holders
        self.pitch_data = np.array([0])
        self.cepstrum_data = np.array([0])
        self.num_display_vals = 300 # TODO: make changeable
        
        # End init
        self.show()

    def cepstrum(self, data):
        hann = np.hanning(len(data))
        return np.absolute(ifft(np.log2(np.absolute(fft(data*hann)))**2))**2
    
    """
    This function is meant for the cepstrum widget when it used alone. If the 
    cesptrum widget is meant to be used with another widget, it is better to 
    feed it data using the observer/listener pattern.
    """
    def detect_pitch(self, file_path = "", play_sound = True):     
        # Open file
        sound_file = file_path
        audio_data = wave.open(sound_file, 'rb')
        
        observable = Observable()
        if play_sound: 
            p = pyaudio.PyAudio()  
            stream = p.open(format = p.get_format_from_width(audio_data.getsampwidth()),  
                            channels = audio_data.getnchannels(),  
                            rate = audio_data.getframerate(),  
                            output = True)
            sound_player = SoundObserver(stream)
            observable.register(sound_player)
        
        data = audio_data.readframes(self.read_length)  
        self.pitch_data = np.array([0])
        while data:  
            observable.update_observers(data) # Play sound
            data = np.fromstring(data, dtype=np.int16)
            
            # Update cepstrum plot
            self.cepstrum_data = self.cepstrum(data)     
            self.cepstrum_data = self.cepstrum_data[0:self.read_length] # Only need one side of the symetrical spectrum
            self.cepstrum_data[:100] = 0 # assume freq < 441
            self.cepstrum_line.setData(range(self.cepstrum_data.shape[0]), self.cepstrum_data)
            
            # Update pitch detection plot
            calc_vol = np.sum(np.abs(data))
            if calc_vol < len(data)*100:
                self.pitch_data = np.append(self.pitch_data, self.pitch_data[-1])
            else:
                self.pitch_data = np.append(self.pitch_data, 44100/np.argmax(self.cepstrum_data))
            self.pitch_line.setData(range(min(self.pitch_data.shape[0], self.num_display_vals)), 
                                self.pitch_data[-self.num_display_vals:])

            # update plots, read data for next loop
            QtGui.QApplication.processEvents() 
            data = audio_data.readframes(self.read_length)
            
    """
    Sound will not be played by this function
    """
    def update_trigger(self, data, clear_flag):
        if clear_flag:
            self.pitch_data = np.array([0])
            return
        
        if not data:
            return
        
        data = np.array(data)
        
        # Update cepstrum plot
        self.cepstrum_data = self.cepstrum(data)     
        self.cepstrum_data = self.cepstrum_data[0:self.read_length] # Only need one side of the symetrical spectrum
        self.cepstrum_data[:100] = 0 # assume freq < 441
        self.cepstrum_line.setData(range(self.cepstrum_data.shape[0]), self.cepstrum_data)
        
        # Update pitch detection plot
        calc_vol = np.sum(np.abs(data))
        if calc_vol < len(data)*1000:
            self.pitch_data = np.append(self.pitch_data, self.pitch_data[-1])
        else:
            self.pitch_data = np.append(self.pitch_data, 44100/np.argmax(self.cepstrum_data))
        self.pitch_line.setData(range(min(self.pitch_data.shape[0], self.num_display_vals)), 
                            self.pitch_data[-self.num_display_vals:])

        QtGui.QApplication.processEvents() 

# Debugging function
if __name__ == "__main__":
   # Needed because pyQT remains in spyder namespace
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    app.exec_()
    
    c_w = CepstrumWidget()
    c_w.detect_pitch(file_path = ".\\singing_samples\\opera_tenor.wav",
        play_sound = True)
        
    c_w.close()
        
