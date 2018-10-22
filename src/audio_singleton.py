import numpy as np
import soundfile as sf

class Singleton:
    """Alex Martelli implementation of Singleton (Borg)
    http://python-3-patterns-idioms-test.readthedocs.io/en/latest/Singleton.html"""
    _shared_state = {}

    def __init__(self):
        self.__dict__ = self._shared_state


class AudioSingleton(Singleton):
    def __init__(self):
        Singleton.__init__(self)

    def get_audio_data(self, idx=0):
        return self.audio_data[self.blocksize*idx:self.blocksize*(idx+1)]

    def get_sample_rate(self):
        return self.sample_rate

    def get_num_blocks(self):
        return int(np.ceil(len(self.audio_data)/self.blocksize))

    def change(self):
        pass # Change audio file

    def load(self, sound_file, dtype, blocksize):
        self.audio_data, self.sample_rate = sf.read(sound_file, dtype = dtype)
        self.blocksize = blocksize
        print(self.sample_rate)


