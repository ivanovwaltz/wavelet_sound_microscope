import itertools as it
import logging

import numpy as np
import scipy
import pysoundfile as sf

from utils import IterableWithLength


log = logging.getLogger(__name__)


class Sound(object):
    pass


def one_channel(wav, channel_num=0):
    return wav[:, channel_num]


class SoundFromSoundFile(Sound):
    def __init__(self, filename):
        self._filename = filename

        with sf.SoundFile(self._filenam) as sound_file:
            self.samplerate = sound_file.samplerate
            self.size = len(sound_file)

        self.duration = self.samplerate / self.size

    @property
    def samples(self):
        return map(one_channel, sf.read(self._filename))

    def get_chunks(self, chunk_size):
        # self.chunks_count = (sound_file.frames - 1) // (chunk_size // 2) + 1
        # FIXME chunk_size or half
        blocks = sf.blocks(self._filename, chunk_size // 2)

        chunks = list(map(one_channel, blocks))
        chunks_count = len(chunks)

        return IterableWithLength(chunks, chunks_count)


class SoundResampled(Sound):
    def __init__(self, original, samplerate):
        self.samplerate = samplerate
        self.size = int(original.size * samplerate / original.samplerate)
        self.samples = scipy.signal.resample(original.samples, self.size)
        self.duration = original.duration

    def get_chunks(self, chunk_size):
        iter_samples = iter(self.samples)
        chunks = map(lambda _: list(it.islice(iter_samples, chunk_size)),
                     it.count())

        return it.takewhile(len, chunks)
