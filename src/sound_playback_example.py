#!/usr/bin/env python3
"""Load an audio file into memory and play its contents.

NumPy and the soundfile module (http://PySoundFile.rtfd.io/) must be
installed for this to work.

This example program loads the whole file into memory before starting
playback.
To play very long files, you should use play_long_file.py instead.

"""
import sounddevice as sd
import soundfile as sf
import time
blocksize = 2048
stream = sd.OutputStream(blocksize=blocksize, device=3, channels=2, dtype='float32')
stream.start()
for blocks in sf.blocks("../singing_samples/a_yeah_yeah.wav", dtype='float32', blocksize=blocksize):
	stream.write(blocks)
	status = sd.wait()
