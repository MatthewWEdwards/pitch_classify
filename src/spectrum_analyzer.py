import numpy as np
import wave
import sounddevice as sd
import soundfile as sf
import yaml
import pyqtgraph as pg
import time
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog
from PyQt5.QtWidgets import QLineEdit
import sys

from observable import Observable
from observers import DisplayObserver, SoundObserver

class SpectrumWidget(QWidget, Observable):
    
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

    def __init__(self):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        
        ### Plot ###
        self.plot = pg.PlotWidget()
        self.layout.addWidget(self.plot, 0, 1, 3, 1) # Main freq graph
        self.setLayout(self.layout)
        self.line = self.plot.plot(pen='y')
        self.plot.setMouseEnabled(False, False)
        ### End Plot ###
        
        ### Buttons ###
        self.play_btn = QPushButton('Play File')
        self.layout.addWidget(self.play_btn, 5, 0)
        self.play_btn.clicked.connect(self.play_click)
        
        self.logbtn = QPushButton('Toggle logscale')
        self.layout.addWidget(self.logbtn, 0, 0)
        self.logbtn.clicked.connect(self.log_click)
        
        self.dec_btn = QPushButton('Toggle dB')
        self.layout.addWidget(self.dec_btn, 1,0)
        self.dec_btn.clicked.connect(self.decible_click)
        
        self.load_btn = QPushButton('Load Audio File')
        self.layout.addWidget(self.load_btn,4,0)
        self.load_btn.clicked.connect(self.load_click)
        self.file_text = QLineEdit()
        self.layout.addWidget(self.file_text, 4, 1)
        self.file_text.setReadOnly(True)
        
        self.pause_btn = QPushButton('Pause Audio')
        self.layout.addWidget(self.pause_btn, 5, 1)
        self.pause_btn.clicked.connect(self.pause_click)
        ### End Buttons ###
        
        self.plot.setXRange(self.freq_range[0], self.freq_range[1])
        self.plot.setYRange(0, 10**6)
        
        self.plot.setLogMode(False, False)
        self.line = self.plot.plot(pen='y')
    
    """
    Loads an audio file. Generates SoundObserver and DisplayObservers to handle
    the data.
    
    Only works for .wav files
    """
    def start_audio(self):
        # Open file
        sound_file = self.file_name
        if sound_file == "":
            return
        audio_data = sf.blocks(sound_file, dtype='float32', blocksize=self.read_length)
        _, self.sample_rate = sf.read(sound_file)
        print(self.sample_rate)
        
        self.play_audio_flag = True
        self.play_audio(audio_data)
    
    """
    audio_data: file object from the output of a call to wave.read()
    TODO: audio_data only accepts .wav files. Make a wrapper class that can
          accept multiple file types.
    """
    def play_audio(self, audio_data):
        self.playing_flag = True
        self.update_observers(clear_flag = True) # Clear plots
        stream = sd.OutputStream(blocksize=self.read_length, channels=2, dtype='float32', samplerate=self.sample_rate)
        stream.start()

        ## Set up Observer-Listeners
        #sound_player = SoundObserver(stream)
        displayer = DisplayObserver(stft_length = self.read_length, 
                        freq_range=self.freq_range, hann=True, sample_freq=self.sample_rate)
        #self.register(sound_player)
        self.register(displayer)
        
        for block in audio_data:
            # If paused
            while not self.play_audio_flag:
                QtGui.QApplication.processEvents() 
                
            if self.quit_flag:
                return

            self.update_observers(data = block)
            
            #########TODO: This section of code has performance issues
            freq_data = displayer.freq_array
            mag_data = displayer.mag_array
            if self.decibles:
                display_data = 20*np.log2(1+mag_data)
            else:
                display_data = mag_data
            self.line.setData(freq_data, display_data)
            #########
            
            while not sd.wait() is None:
                pass
            
            stream.write(block)

            QtGui.QApplication.processEvents() 
            self.signal.emit(block.tolist(), False, self.sample_rate)
            
        #self.unregister(sound_player)
        self.unregister(displayer)

        self.playing_flag = False
        
    def clear(self):
        self.signal.emit([], True, 0)
        
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

    def load_click(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.file_name, _ = QFileDialog.getOpenFileName(self,
            "Select .wav file", "","(*.wav)", options=options)
        self.file_text.setText(self.file_name) 
        
    def play_click(self):
        if not self.playing_flag:
            self.clear()
            self.start_audio()
    
    def pause_click(self):
        self.play_audio_flag = not self.play_audio_flag
        
    def quit_audio(self):
        self.quit_flag = not self.quit_flag
        self.play_audio_flag = True # Forces play loop to continue to allow for quitting
    """
    End button functions
    """

        
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
        
