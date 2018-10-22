from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton
import sys

from spectrum_analyzer import SpectrumWidget
#from cepstrum import CepstrumWidget
from pitch_widget import PitchWidget
from note_widget import NoteWidget
from system_widget import SystemWidget
from audio_singleton import AudioSingleton

class MultiWidget(QWidget):

    exist = True
    
    def __init__(self, spec = None, pitch = None, note = None, sys_w = None):
        super(QWidget, self).__init__()
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        self.audio_singleton = AudioSingleton()
            
        if spec is None:
            spec = SpectrumWidget()
        if pitch is None:
            pitch = PitchWidget()
#        if note is None:
#            note = NoteWidget()
        if sys_w is None:
            sys_w = SystemWidget([spec, pitch], quit=False)

        self.widgets = [sys_w, spec, pitch]

        for widget in range(len(self.widgets)):
            self.layout.addWidget(self.widgets[widget], widget, 0)
        
        self.quit_btn = QPushButton('Quit')
        self.layout.addWidget(self.quit_btn, 4, 0)
        self.quit_btn.clicked.connect(self.quit)

    def quit(self):
        sys_w.quit()
        self.close()
        self.exist = False
        
if __name__ == '__main__':
    # Needed because pyQT remains in spyder namespace
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    m_w = MultiWidget()
    m_w.show()
    while m_w.exist:
        QtGui.QApplication.processEvents()
    m_w.close()
    logscale = False
    decibles = False
    hann = True
    playing_flag = False
        
