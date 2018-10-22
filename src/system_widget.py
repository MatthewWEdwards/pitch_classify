import sounddevice as sd
import soundfile as sf
import numpy as np
import sys
import yaml
import multiprocessing
import ctypes
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog, QLineEdit

from observable import Observable
from observers import SoundObserver

# TODO Am I actually going to use this class
class DataHolder():
    def __init__(self):
        self.data = np.array((0,))
        self.sample_rate = 44100

    def update(self, data, sample_rate=None):
        self.data = data
        if not sample_rate is None:
            self.sample_rate = sample_rate

class SystemWidget(QWidget, Observable):
    playing_flag = False
    config = yaml.load(open('../config.yaml', 'rb').read())
    file_name = ""
    read_length = config['read_length']
    sample_rate = 44100
    play_audio_flag = False
    quit_flag = False
    data_holder = DataHolder()
    exist = True
    
    def __init__(self, observers, quit=False):
        super(QWidget, self).__init__()

        self.layout = QtWidgets.QGridLayout()
    
        ### Buttons ###
        self.play_btn = QPushButton('Play File')
        self.layout.addWidget(self.play_btn, 5, 0)
        self.play_btn.clicked.connect(self.play_click)
        
        self.load_btn = QPushButton('Load Audio File')
        self.layout.addWidget(self.load_btn,4,0)
        self.load_btn.clicked.connect(self.load_click)
        self.file_text = QLineEdit()
        self.layout.addWidget(self.file_text, 4, 1)
        self.file_text.setReadOnly(True)
        
        self.pause_btn = QPushButton('Pause Audio')
        self.layout.addWidget(self.pause_btn, 5, 1)
        self.pause_btn.clicked.connect(self.pause_click)

        if quit:
            self.quitbtn = QPushButton('Quit')
            self.layout.addWidget(self.quitbtn, 6, 0)
            self.quitbtn.clicked.connect(self.quit)
        ### End Buttons ###

        self.setLayout(self.layout)
        self.show()

        ### Set up Observer-Listeners ###
        for observer in observers:
            self.register(observer)

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
    
    def play_audio(self, audio_data):
        self.playing_flag = True
        self.update_observers(clear_flag = True) # Clear plots
        # TODO: set "channels" based on the content of the audio file
        stream = sd.OutputStream(blocksize=self.read_length, channels=2, 
            dtype='float32', samplerate=self.sample_rate)
        stream.start()

        for block in audio_data:
            # If paused
            while not self.play_audio_flag:
                QtWidgets.QApplication.processEvents() 
            # Stop if the app quits
            if self.quit_flag:
                return
            # Wait for audio to finish playing
            while not sd.wait() is None:
                QtWidgets.QApplication.processEvents() 
            self.update_observers(data = block)
            stream.write(block)
            #data = multiprocessing.Array(data, lock=False) # read-only data, lock can be false
            
            QtWidgets.QApplication.processEvents() 
            
        self.playing_flag = False

    def load_click(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        self.file_name, _ = QFileDialog.getOpenFileName(self,
            "Select .wav file", "","(*.wav)", options=options)
        self.file_text.setText(self.file_name) 
        
    def play_click(self):
        if not self.playing_flag:
            self.start_audio()
    
    def pause_click(self):
        self.play_audio_flag = not self.play_audio_flag
        
    def quit_audio(self):
        self.quit_flag = not self.quit_flag
        self.play_audio_flag = True # Forces play loop to continue to allow for quitting

    def quit(self):
        self.unregister_all()
        self.quit_audio()
        self.exist = False
        self.close()

if __name__ == "__main__":
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
        
    widget = SystemWidget([], quit=True)
    widget.show()
    while widget.exist:
        QtWidgets.QApplication.processEvents()
    widget.close()

    sys.exit(0)
        

