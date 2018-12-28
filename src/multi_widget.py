from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton
import sys

from spectrum_analyzer import SpectrumWidget
from pitch_widget import PitchWidget
from note_widget import NoteWidget
from system_widget import SystemWidget
from audio_singleton import AudioSingleton

class MultiWidget(QtWidgets.QMainWindow):

    def __init__(self, spec = None, pitch = None, note = None, sys_w = None):
        super().__init__()
        self.setObjectName("MainWindow")
        self.setWindowTitle("Pitch Classify")
        
        self.w = QtWidgets.QWidget()
        self.setCentralWidget(self.w)
        self.layout = QtGui.QGridLayout(self.w)
        self.setLayout(self.layout)

        self.audio_singleton = AudioSingleton()
            
        if spec is None:
            spec = SpectrumWidget()
        self.spec_gbox = QtWidgets.QGroupBox("Spectrum")
        self.spec_gbox_l = QtWidgets.QGridLayout(self.spec_gbox)
        self.spec_gbox_l.addWidget(spec)
        self.layout.addWidget(self.spec_gbox, 2, 0, 8, 8)

        if note is None:
            note = NoteWidget()
        self.note_gbox = QtWidgets.QGroupBox("Note Plot")
        self.note_gbox_l = QtWidgets.QGridLayout(self.note_gbox)
        self.note_gbox_l.addWidget(note)
        self.layout.addWidget(self.note_gbox, 0, 8, 4, 2)

        if pitch is None:
            pitch = PitchWidget(note_widget = note)
        self.pitch_gbox = QtWidgets.QGroupBox("Pitch Plot")
        self.pitch_gbox_l = QtWidgets.QGridLayout(self.pitch_gbox)
        self.pitch_gbox_l.addWidget(pitch)
        self.layout.addWidget(self.pitch_gbox, 4, 8, 4, 1)

        if sys_w is None:
            sys_w = SystemWidget([spec, pitch], quit=False)
        self.sys_gbox = QtWidgets.QGroupBox("System Control")
        self.sys_gbox_l = QtWidgets.QGridLayout(self.sys_gbox)
        self.sys_gbox_l.addWidget(sys_w)
        self.layout.addWidget(self.sys_gbox, 0, 0, 1, 1)

        self.quit_btn = QPushButton('Quit')
        self.layout.addWidget(self.quit_btn, 1, 0, 1, 1)
        self.quit_btn.clicked.connect(self.quit)

    def closeEvent(self, event):
        """ Called when the PyQt window is closed. Inherited from QtWidgets.QWidget.
        
            Args:
                event (QCloseEvents): The PyQt event which triggered this function.
        """
        sys.exit(app.exec_())


    def quit(self):
        sys.exit(app.exec_())
        
if __name__ == '__main__':
    myApp = QtWidgets.QApplication.instance()
    if myApp is None:
        args = list(sys.argv)
        #args[1:1] = ['-stylesheet', stylesheet_fname]
        myApp = QtWidgets.QApplication(args)
    myWin = MultiWidget()
    myWin.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtWidgets.QApplication.instance().exec_()

