import numpy as np
import wave
import pyaudio
import pyqtgraph as pg
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget
import sys

from observable import Observable
from observers import SoundObserver
from scipy.fftpack import fft, ifft

class CepstrumWidget(QWidget):
    
    def __init__(self):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        # Defaults              
        self.read_length = 2**10
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
        self.pitch_plot.setYRange(0, 2000)
        
        self.show()

    def cepstrum(self, data):
        return np.absolute(ifft(np.log2(np.absolute(fft(data)))**2))**2
    

    def detect_pitch(self):     
        # Open file
        sound_file = ".\\singing_samples\\opera_tenor.wav"
        audio_data = wave.open(sound_file, 'rb')
        
        p = pyaudio.PyAudio()  
        stream = p.open(format = p.get_format_from_width(audio_data.getsampwidth()),  
                        channels = audio_data.getnchannels(),  
                        rate = audio_data.getframerate(),  
                        output = True)              
        
        # Set up Observer-Listeners
        observable = Observable()
        sound_player = SoundObserver(stream)
        #TODO: Make customizable
        observable.register(sound_player)
            
        data = audio_data.readframes(self.read_length)  
        pitch_data = np.ndarray([])
        while data:  
            observable.update_observers(data)
            data = np.fromstring(data, dtype=np.int16)


            # Update cepstrum plot
            cepstrum_data = self.cepstrum(data)     
            cepstrum_data = cepstrum_data[0:self.read_length] # Only need one side of the symetrical spectrum
            self.cepstrum_line.setData(range(cepstrum_data.shape[0]), cepstrum_data)
            
            # Update pitch detection plot
            pitch_data = np.append(pitch_data, 44100/np.argmax(cepstrum_data[100:1000]))
            self.pitch_line.setData(range(pitch_data.shape[0]), pitch_data)
            print 44100/np.argmax(cepstrum_data[100:1000]) # TODO: Debugging

            QtGui.QApplication.processEvents() 
            data = audio_data.readframes(self.read_length)


if __name__ == "__main__":
   # Needed because pyQT remains in spyder namespace
    if not QtGui.QApplication.instance():
        app = QtGui.QApplication([])
    else:
        app = QtGui.QApplication.instance() 
    app.exec_()
    
    c_w = CepstrumWidget()
    c_w.detect_pitch()
        
    c_w.close()
    sys.exit(app.exec_())
        
