import numpy as np
import pyqtgraph as pg
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PyQt5.QtWidgets import QSpinBox, QSlider
from PyQt5.QtCore import pyqtSlot

from observers import DisplayObserver as dis

class FilePlayer(QWidget):
    
    def __init__(self, DisplayObserver):
        QtGui.QWidget.__init__(self)
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        self.plot = 
        self.layout.addWidget(DisplayObserver, 0, 0)
        self.show()
        
    @pyqtSlot()
    
    # Button functions
    def log_click(self):
        self.logscale = not self.logscale
        self.plot.setLogMode(self.logscale, False)
        if self.logscale:
            self.plot.setXRange(np.log10(self.freq_range[0]+1), 
                                np.log10(self.freq_range[1]))
        else:
            self.plot.setXRange(self.freq_range[0], self.freq_range[1])
        
        # Idk why this is necessary here but it is
        if self.decibles:
            self.plot.setYRange(0,150)
        else:
            self.plot.setYRange(0, 10**6)
            
    def decible_click(self):
        self.decibles = not self.decibles
        self.plot.setLogMode(self.logscale, False)
        if self.decibles:
            self.plot.setYRange(0,150)
        else:
            self.plot.setYRange(0, 10**6)
        
        # Idk why this is necessary here but it is
        if self.logscale:
            self.plot.setXRange(np.log10(self.freq_range[0]+1), 
                                np.log10(self.freq_range[1]))
        else:
            self.plot.setXRange(self.freq_range[0], self.freq_range[1])
            
# Plot Test
if __name__ == "__main__":
   # Needed because pyQT remains in spyder namespace
    app = None
    if not QtGui.QApplication.instance():
        app = QtGui.QApplication([])
    else:
        app = QtGui.QApplication.instance() 
        
    app.exec_()
    
    player = FilePlayer(dis())

    while True:
        pass