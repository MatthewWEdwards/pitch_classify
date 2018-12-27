import numpy as np
from PyQt5 import QtGui
from PyQt5.QtGui import QPixmap 
from PyQt5.QtWidgets import QWidget, QLabel
import pyqtgraph as pg
import yaml
import traceback
import sys

from observer import Observer

from noconflict import classmaker

class NoteWidget(QWidget, Observer):
    _metaclass_ = classmaker()
    current_note = "N"
    image_width = 100
    image_height = 100
    letter_images_path = "../letters/"
    num_display_vals = 100
    
    def __init__(self):
        super(QWidget, self).__init__()
        
        self.layout = QtGui.QGridLayout()
        self.setLayout(self.layout)

        # Config
        self.config = yaml.load(open('config.yaml', 'rb').read())
        
        # Plot
        self.note_plot = pg.PlotWidget()
        self.layout.addWidget(self.note_plot, 0, 0)
        self.note_line = self.note_plot.plot(pen='y')
        self.note_plot.setMouseEnabled(False, False)
        self.note_plot.setYRange(0, 13)
        
        # Letter display
        self.letter_display = QLabel()
        self.letter_display.resize(self.image_width, self.image_height)
        self.pixmap = QPixmap(self.image_width, self.image_height)
        self.layout.addWidget(self.letter_display, 0, 1)
        
        # Init Holders
        self.note_data = np.array([0])
        self.num_display_vals = self.config['note']['num_display'] 
        
        # End init
        self.show()
        
    def hz_to_midi(self, freq):
        if freq <= 20:
            freq = 20.0
        if freq == np.inf:
            freq = 20.0
        freq = float(freq)
        return 69 + 12*np.log2(freq/440.0)
    
    def get_note(self, freq):
        index = int(self.hz_to_midi(freq))
        if index >= len(midi_table) or index < 0:
            return midi_table[12] # TODO return an error code
        return midi_table[index]
    
    def get_plot_val(self, freq):
        note = letter_map[self.get_note(freq)]
        return float(note) + (self.hz_to_midi(freq) % 1)
    
    def update(self, *args, **kwargs):
        try:
            freq = kwargs.get('freq', 44100)
            clear_flag = kwargs.get('clear_flag', False)
            if clear_flag:
                self.note_data = np.array([0])
                return
            
            note = self.get_note(freq)
            
            # Update letter image
            note_name = note[0]
            if note.find("#") != -1:
                note_name = note_name + "_sharp"
            self.pixmap.load(self.letter_images_path + note_name)
            self.letter_display.setPixmap(self.pixmap)
            
            # Update plot
            self.note_data = np.append(self.note_data, self.get_plot_val(freq))
            self.note_line.setData(range(min(self.note_data.shape[0], self.num_display_vals)), 
                                self.note_data[-self.num_display_vals:])
        except Exception as e:
            print(e)
            print(''.join(traceback.format_tb(e.__traceback__)))
            sys.exit()
    
midi_table = {
    12: "C",
    13: "C#",
    14: "D",
    15: "D#",
    16: "E",
    17: "F",
    18: "F#",
    19: "G",
    20: "G#",
    21: "A",
    22: "A#",
    23: "B",
    24: "C",
    25: "C#",
    26: "D",
    27: "D#",
    28: "E",
    29: "F",
    30: "F#",
    31: "G",
    32: "G#",
    33: "A",
    34: "A#",
    35: "B",
    36: "C",
    37: "C#",
    38: "D",
    39: "D#",
    40: "E",
    41: "F",
    42: "F#",
    43: "G",
    44: "G#",
    45: "A",
    46: "A#",
    47: "B",
    48: "C",
    49: "C#",
    50: "D",
    51: "D#",
    52: "E",
    53: "F",
    54: "F#",
    55: "G",
    56: "G#",
    57: "A",
    58: "A#",
    59: "B",
    60: "C",
    61: "C#",
    62: "D",
    63: "D#",
    64: "E",
    65: "F",
    66: "F#",
    67: "G",
    68: "G#",
    69: "A",
    70: "A#",
    71: "B",
    72: "C",
    73: "C#",
    74: "D",
    75: "D#",
    76: "E",
    77: "F",
    78: "F#",
    79: "G",
    80: "G#",
    81: "A",
    82: "A#",
    83: "B",
    84: "C",
    85: "C#",
    86: "D",
    87: "D#",
    88: "E",
    89: "F",
    90: "F#",
    91: "G",
    92: "G#",
    93: "A",
    94: "A#",
    95: "B"
}

letter_map = {
    "A" : 0,
    "A#": 1,
    "B" : 2,
    "C" : 3,
    "C#": 4,
    "D" : 5,
    "D#": 6,
    "E" : 7,
    "F" : 8,
    "F#": 9,
    "G" : 10,
    "G#": 11
        }
