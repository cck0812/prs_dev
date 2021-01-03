#!/usr/bin/python
# -*- coding: utf-8 -*-
import hashlib
import itertools
import logging
import os
import re
from fileinput import FileInput, hook_encoded
from functools import reduce

from configs.setup_settings import CFGSettings


class CRLogHandler:
    cr_id_pattern = r"^(?:DTV)\d+"
    CONFIG_SET = ["pattern_meta"]

    def __init__(self, path):
        self.logger = logging.getLogger(__name__)
        self.conf = CFGSettings().load_conf(conf_folder=True)
        self.conf = {cs: getattr(self.conf, cs) for cs in self.CONFIG_SET}

        self.base_filename = os.path.basename(path)
        self.filename = None
        self.path = path
        self.hashpath = hashlib.md5(self.path.encode("utf-8")).hexdigest()
        self.file = None
        self.line_counts = None
        self.cr_id = None
        self.is_autolog = False

    def _fetch(self):
        encoding = "utf-8"
        errors = "surrogateescape"
        chunk_size = self.conf["file"]["src_chunk_size"]

        fobj = FileInput(self.path, openhook=hook_encoded(encoding, errors))
        chunks = self.chunks(fobj, size=chunk_size)
        self.file = chunks

        return self

    def __enter__(self):
        return self._fetch()

    def __exit__(self):
        self.file.close()
        self.logger.debug(f"{self.path} was closed.")

    def get_filename(self):
        # example: DTV03036540-2020-10-28-015510-bsp_common_common.sh_90001-kernel.log

        if self.base_filename.startswith("DTV"):
            m_obj = re.search(self.cr_id_pattern, self.base_filename)
            if m_obj:
                self.cr_id = m_obj.group(0)
                self.filename = re.sub(self.cr_id + "-", "", self.base_filename)
        else:
            self.filename = self.base_filename

        return self.filename

    def is_from_autolog(self):
        if self.filename is None:
            self.get_filename()

        autolog_fmt = reduce(dict.get, ["log_format", "autolog", "filename_format"])
        is_autolog = re.search(autolog_fmt, self.filename)
        if is_autolog:
            self.is_autolog = True

        return self.is_autolog

    def get_line_counts(self):
        if self.file:
            return len(self.file)
        else:
            return None

    def collect(self):
        collection = dict(
            result_list=[],
            is_autolog=self.is_from_autolog(),
            filename=self.get_filename(),
            cr_id=self.cr_id,
        )

        return {self.hashpath: collection}

    def update_queue_to_shm(self, shm, manager):
        parsers = self.conf["registered_parser"]
        parsers_name = list(map(lambda d: list(d.keys())[0], parsers))
        for pn in parsers_name:
            shm[self.hashpath].update({pn: manager.Queue()})

    def chunks(self, iterable, size=0):
        if size == 0:
            return iterable
        else:
            iterator = iter(iterable)
            for first in iterator:
                yield itertools.chain([first], itertools.islice(iterator, size - 1))


def main():
    path = "H:\mtk_project\prs_dev\example\DTV03036540-2020-10-28-015510-bsp_common_common.sh_90001-kernel.log"


if __name__ == "__main__":
    main()
