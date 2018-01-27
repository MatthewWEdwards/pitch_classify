import numpy as np
import wave
import pyaudio  
import yaml
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog
from PyQt5.QtWidgets import QLineEdit
import sys
from threading import Condition, Thread

from observable import Observable
from observers import DisplayObserver, SoundObserver

class SpectrumWidget(QWidget, Observable):
    
    signal = QtCore.pyqtSignal(list, bool)
    playing_flag = False

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
        self.playbtn = QPushButton('Play File')
        self.layout.addWidget(self.playbtn, 5, 0)
        self.playbtn.clicked.connect(self.play_click)
        
        self.logbtn = QPushButton('Toggle logscale')
        self.layout.addWidget(self.logbtn, 0, 0)
        self.logbtn.clicked.connect(self.log_click)
        
        self.decbtn = QPushButton('Toggle dB')
        self.layout.addWidget(self.decbtn, 1,0)
        self.decbtn.clicked.connect(self.decible_click)
        
        self.loadbtn = QPushButton('Load Audio File')
        self.layout.addWidget(self.loadbtn,4,0)
        self.loadbtn.clicked.connect(self.load_click)
        self.filetext = QLineEdit()
        self.layout.addWidget(self.filetext, 4, 1)
        self.filetext.setReadOnly(True)
        
        self.pausebtn = QPushButton('Pause Audio')
        self.layout.addWidget(self.pausebtn, 5, 1)
        self.pausebtn.clicked.connect(self.pause_click)
        ### End Buttons ###
        
        ### Defaults ###
        config = yaml.load(file('..\\config.yaml', 'rb').read())
        self.logscale = False
        self.decibles = False
        self.freq_range = [config['plots']['freq_min'], config['plots']['freq_max']]
        self.fileName = ""
        self.read_length = config['read_length'] # TODO: Make customizable
        self.playaudioflag = False
        self.playaudiocond = Condition()
        
        self.plot.setXRange(self.freq_range[0], self.freq_range[1])
        self.plot.setYRange(0, 10**6)
        
        self.plot.setLogMode(False, False)
        self.line = self.plot.plot(pen='y')
        ### End Defaults ###
        
        self.show()
    
    """
    Loads an audio file. Generates SoundObserver and DisplayObservers to handle
    the data.
    
    Only works for .wav files
    """
    def start_audio(self):
        # Open file
        sound_file = self.fileName
        if sound_file == "":
            return
        audio_data = wave.open(sound_file, 'rb')
        
        self.playaudioflag = True
        self.play_audio(audio_data)
        #self.audiothread = Thread(target = self.play_audio, args = (audio_data, ))
        #self.audiothread.start()
    
    """
    audio_data: file object from the output of a call to wave.read()
    TODO: audio_data only accepts .wav files. Make a wrapper class that can
          accept multiple file types.
    """
    def play_audio(self, audio_data):
        self.playing_flag = True
        self.update_observers(clear_flag = True) # Clear plots
        p = pyaudio.PyAudio()  
        stream = p.open(format = p.get_format_from_width(audio_data.getsampwidth()),  
                        channels = audio_data.getnchannels(),  
                        rate = audio_data.getframerate(),  
                        output = True)  
        
        # Set up Observer-Listeners
        sound_player = SoundObserver(stream)
        #TODO: Make customizable
        displayer = DisplayObserver(stft_length = self.read_length, 
                        freq_range=self.freq_range, hann=True)
        self.register(sound_player)
        self.register(displayer)
        
        data = audio_data.readframes(self.read_length)      
        while data:  
            
            self.playaudiocond.acquire()
            if not self.playaudioflag:
                self.playaudiocond.wait()
                
            self.update_observers(data = data)
            disp_data = displayer.graph_data
            # Difference here done for efficiency reasons (RE: Pandas)
            if self.decibles:
                self.line.setData(disp_data['freq'].as_matrix(), 20*np.log2(1+disp_data['magnitude']).as_matrix())
            else:
                self.line.setData(disp_data['freq'].as_matrix(), disp_data['magnitude'].as_matrix())
           
            QtGui.QApplication.processEvents() 
            self.playaudiocond.release()
            data = audio_data.readframes(self.read_length)  
            data_list = list(np.fromstring(data, dtype=np.int16))
            self.signal.emit(data_list, False)
            
        self.unregister(sound_player)
        self.unregister(displayer)
        p.close(stream)
        self.playing_flag = False
        
    # Button functions
    def log_click(self):
        self.logscale = not self.logscale
        self.plot.setLogMode(self.logscale, False)
        
        if self.logscale:
            self.plot.setXRange(np.log2(self.freq_range[0]+1), 
                                np.log2(self.freq_range[1]+1))
        else:
            self.plot.setXRange(self.freq_range[0], self.freq_range[1])
        
        # Idk why this is necessary here but it is
        if self.decibles:
            self.plot.setYRange(0,340)
        else:
            self.plot.setYRange(0, 10**6)
            
    def decible_click(self):
        self.decibles = not self.decibles
        if self.decibles:
            self.plot.setYRange(0,340) # TODO: make this actually based on data
        else:
            self.plot.setYRange(0, 10**6)

        
    def load_click(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.fileName, _ = QFileDialog.getOpenFileName(self,"Select .wav file", "","(*.wav)", options=options)
        self.filetext.setText(self.fileName) 
        
    def play_click(self):
        if not self.playing_flag:
            self.start_audio()
    
    def pause_click(self):
        if not self.playaudioflag:
            self.playaudiocond.acquire()
            self.playaudiocond.notify()
            self.playaudiocond.release()
        self.playaudioflag = not self.playaudioflag
        
        
if __name__ == "__main__":
   # Needed because pyQT remains in spyder namespace
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        
        
    app.exec_()
    s_w = SpectrumWidget()
    while True:
        QtGui.QApplication.processEvents()
    s_w.close()

    sys.exit(app.exec_())
        
