import logging

import numpy as np
from pysoundfile import SoundFile
from scipy.misc import toimage

from .media import apply_colormap, wav_chunks_from_sound_file, nolmalize_horizontal_smooth
from .wavelet.cuda_backend import WaveletBox
from utils import cached_property, IterableWithLength


log = logging.getLogger(__name__)


class Composition(object):
    def __init__(self, filename):
        self.filename = filename
        self.sound_file = SoundFile(self.filename)

        self.nsamples = 2 ** (
            1 + int(np.log2(self.sound_file.sample_rate - 1))
        )

        self.decimation_factor = 8
        self.decimate = self.nsamples // 2 ** self.decimation_factor

        log.debug('Bitrate: %s', self.sound_file.sample_rate)
        log.debug('Sound samples: %s', self.sound_file.frames)
        log.debug('Fragment samples: %s', self.nsamples)

        self.norma_window_len = 501
        log.debug('Norma window len: %s', self.norma_window_len)

    def prepare_wbox(self):
        return self.wbox

    @cached_property
    def wbox(self):
        return WaveletBox(self.nsamples, time_step=1,
                          scale_resolution=1 / 72, omega0=70)

    @cached_property
    def whole_image(self):
        return self.get_whole_image(self.get_wav_chunks(),
                                    decimate=self.decimate)

    def get_whole_image(self, chunks, decimate):
        return self.wbox.apply_cwt(chunks, decimate=decimate)

    def get_wav_chunks(self):
        return IterableWithLength(
            wav_chunks_from_sound_file(self.sound_file, self.nsamples // 2),
            self.chunks_count
        )

    @cached_property
    def chunks_count(self):
        count = (self.sound_file.frames - 1) // (self.nsamples // 2) + 1
        log.debug('Chunks count: %s', count)

        return count

    def get_image(self, norma_window_len=None):
        abs_image = np.abs(self.whole_image)

        if norma_window_len:
            nolmalize_horizontal_smooth(abs_image, norma_window_len)

        return toimage(apply_colormap(abs_image))


class CompositionWithProgressbar(Composition):
    def __init__(self, fname, progressbar):
        self.progressbar = progressbar
        super().__init__(fname)

    def get_whole_image(self, chunks, decimate):
        with self.progressbar(chunks) as chunks_:
            return super().get_whole_image(chunks_, decimate)