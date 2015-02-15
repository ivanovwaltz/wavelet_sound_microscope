import logging
import os
from functools import partial

from PIL.Image import Image
from PyQt5.QtCore import QObject, pyqtSignal, QThread

from .threading import QThreadedWorkerDebug as QThreadedWorker
from utils import ProgressProxy


log = logging.getLogger(__name__)


class ProgressProxyToProgressDialog(ProgressProxy):
    def __init__(self, progress_dialog, *args, **kwargs):
        self.progress_dialog = progress_dialog
        super().__init__(*args, **kwargs)

    def start(self):
        self.progress_dialog.reset()
        self.progress_dialog.setRange(0, self.length)

    def render_progress(self):
        self.progress_dialog.setValue(self.pos)


class QCompositionWorker(QThreadedWorker):
    def __init__(self, progress_dialog):
        super().__init__()

        self.progress_dialog = progress_dialog

        self.load_file.connect(self._load_file)
        self.process.connect(self._process)

    load_file = pyqtSignal(str)
    load_file_ok = pyqtSignal()
    load_file_error = pyqtSignal()

    process = pyqtSignal()
    process_ok = pyqtSignal(Image)

    message = pyqtSignal(str)

    def set_progress_value(self, val):
        self._message('Progress value: {}'.format(val))

    def _load_file(self, fname):
        self._message('Loading...')

        from analyze.composition import CompositionWithProgressbar

        log.info('CompositionWorker._load_file: %s', fname)

        self.fname = fname

        progressbar = partial(ProgressProxyToProgressDialog,
                              self.progress_dialog)

        try:
            self.composition = CompositionWithProgressbar(fname, progressbar)

        except Exception as e:
            log.error('Create composition error: %s', repr(e))
            self._message(repr(e))
            self.load_file_error.emit()

            return

        else:
            log.info('Create composition ok')
            self._message('Opened {0}'.format(os.path.basename(fname)))
            self.load_file_ok.emit()

    def _process(self):
        log.debug('Before Image processed')

        self._message('Prepare composition Wavelet Box')
        self.composition.prepare_wbox()

        self._message('Analyse')
        image = self.composition.get_image()
        log.debug('Image processed')
        self.process_ok.emit(image)
        self._message('Done')

    def _message(self, msg):
        self.message.emit(msg)
