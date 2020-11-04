#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import json
import codecs
import logging
from datetime import datetime
from fileinput import FileInput, hook_encoded
from utils.result_collector import FinalResultCollector


class CRLogHandler():
    mode = 'r'
    encoding = 'utf-8'
    err_to_read = 'surrogateescape'
    cr_id_pattern = r'^(?:DTV)\d+'

    def __init__(self, path, obj):
        self.logger = logging.getLogger(__name__)
        self.base_filename = os.path.basename(path)
        self.path = path
        self.created_time = None
        self.finished_time = None
        self.parser_time = None
        self.file_obj = None
        self.col_obj = obj
        self.line_count = None
        self.cr_id = None
        self.is_autolog = False

    def _open(self):
        encoding = CRLogHandler.encoding
        errors = CRLogHandler.err_to_read
        self.file_obj = FileInput(self.path, openhook=hook_encoded(encoding, errors))
        self.created_time = datetime.now()

        return self

    def __enter__(self):
        self.get_cr_id_from_filename()
        self.is_from_autolog()

        return self._open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.line_count = self.file_obj.lineno()
        except AttributeError as err:
            self.logger.error(err.args)

        self.file_obj.close()
        self.finished_time = datetime.now()
        self.parser_time = self.finished_time - self.created_time
        self.logger.info(f"Filename: {self.base_filename} was closed !!")
        attrs = vars(self)
        self.col_obj.__dict__.update(attrs)

    def get_cr_id_from_filename(self):
        # example: DTV03036540-2020-10-28-015510-bsp_common_common.sh_90001-kernel.log

        cr_id_pattern = self.cr_id_pattern
        m_obj = re.search(cr_id_pattern, self.base_filename)
        if m_obj:
            self.cr_id = m_obj.group(0)

        return self.cr_id

    def is_from_autolog(self):
        cr_id = self.get_cr_id_from_filename()
        crid_suffix = cr_id + '-'
        autolog_fmt = r"^\d{4}-\d{2}-\d{2}-\d{6}-.*\.(?:log)$"

        if cr_id:
            new_fn = re.sub(crid_suffix, "", self.base_filename)
            setattr(self, 'filename', new_fn)

            is_autolog = re.search(autolog_fmt, new_fn)
            if is_autolog:
                self.is_autolog = True

        return self.is_autolog


def main():
    path = 'H:\mtk_project\prs_dev\example\DTV03036540-2020-10-28-015510-bsp_common_common.sh_90001-kernel.log'
    result = FinalResultCollector()
    with CRLogHandler(path, result) as file_obj:
        print(file_obj)
    print()
    print(vars(result))

if __name__ == '__main__':
    main()