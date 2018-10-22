import sounddevice as sd
import numpy as np
import yaml
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton, QFileDialog, QLineEdit

from observable import Observable
from audio_singleton import AudioSingleton

class SystemWidget(QWidget, Observable):
    playing_flag = False
    play_audio_flag = False
    quit_flag = False
    exist = True
    config = yaml.load(open('../config.yaml', 'rb').read())
    
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

        self.audio_singleton = AudioSingleton()

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
        sound_file = self.file_text.text()
        if sound_file == "":
            return
        self.audio_singleton.load(sound_file, "float32", self.config['read_length'])
        self.play_audio_flag = True
        self.play_audio()
    
    def play_audio(self):
        self.playing_flag = True
        self.update_observers(clear_flag = True) # Clear plots
        # TODO: set "channels" based on the content of the audio file
        # TODO: Device index hardcoded
        stream = sd.OutputStream(blocksize=self.config['read_length'], channels=2, 
            dtype='float32', samplerate=self.audio_singleton.get_sample_rate(), device=3)
        stream.start()
        
        for block_idx in range(self.audio_singleton.get_num_blocks()):
            # If paused
            while not self.play_audio_flag:
                QtWidgets.QApplication.processEvents() 
            # Stop if the app quits
            if self.quit_flag:
                return
            # Wait for audio to finish playing
            while not sd.wait() is None:
                QtWidgets.QApplication.processEvents() 
            stream.write(self.audio_singleton.get_audio_data(idx=block_idx))
            self.update_observers(data = block_idx) 
            
        self.playing_flag = False
        stream.close()

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

