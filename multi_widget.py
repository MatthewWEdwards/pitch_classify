import pandas
import numpy as np
import wave
import pyaudio  
import pyqtgraph as pg
from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PyQt5.QtWidgets import QFileDialog, QLineEdit
from PyQt5.QtCore import pyqtSlot
import sys
from threading import Thread, Event, Condition, Semaphore

from observable import Observable
from observers import DisplayObserver, SoundObserver
from spectrum_analyzer import SpectrumWidget
from cepstrum import CepstrumWidget

class SpectrumCepstrum(QWidget):

    def __init__(self, spec = SpectrumWidget(), ceps = CepstrumWidget()):
        super(QWidget, self).__init__()
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        self.spec = spec
        self.ceps = ceps
        
        spec.signal.connect(ceps.update_trigger)

        self.layout.addWidget(self.spec, 0, 0)
        self.layout.addWidget(self.ceps, 1, 0)
        
        self.show()
        
        
if __name__ == '__main__':
    # Needed because pyQT remains in spyder namespace
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    app.exec_()
    
    m_w = SpectrumCepstrum()
    while True:
        QtGui.QApplication.processEvents()
        
    m_w.close()
        