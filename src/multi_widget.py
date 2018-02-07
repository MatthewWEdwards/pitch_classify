from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtWidgets import QWidget, QPushButton
import sys

from spectrum_analyzer import SpectrumWidget
from cepstrum import CepstrumWidget
from yin_personal import YinWidget

class MultiWidget(QWidget):

    exist = True
    
    def __init__(self, spec = SpectrumWidget(), ceps = CepstrumWidget(),
                 yin = YinWidget()):
        super(QWidget, self).__init__()
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)
        
        self.spec = spec
        self.ceps = ceps
        self.yin = yin
        
        spec.signal.connect(ceps.update_trigger)
        spec.signal.connect(yin.update_trigger)

        self.layout.addWidget(self.spec, 0, 0)
        self.layout.addWidget(self.ceps, 1, 0)
        self.layout.addWidget(self.yin, 2, 0)       
        
        self.quitbtn = QPushButton('Quit')
        self.layout.addWidget(self.quitbtn, 3, 0)
        self.quitbtn.clicked.connect(self.quit)

    def quit(self):
        self.spec.quit_audio()
        self.close()
        self.exist = False
        
if __name__ == '__main__':
    # Needed because pyQT remains in spyder namespace
    app = QtCore.QCoreApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    app.exec_()
    
    m_w = MultiWidget()
    m_w.show()
    while m_w.exist:
        QtGui.QApplication.processEvents()
        
    m_w.close()
        