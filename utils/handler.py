#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import json
import codecs
import logging
from fileinput import FileInput, hook_encoded


class CRLogHandler():
    mode = 'r'
    encoding = 'utf-8'
    err_to_read = 'surrogateescape'
    cr_id_pattern = r'^(?:DTV)\d+'

    def __init__(self, path):
        self.logger = logging.getLogger(__name__)
        self.base_filename = os.path.basename(path)
        self.path = path
        self.file_obj = None
        self.file_len = None
        self.cr_id = None 
        self.is_autolog = False
        self.logfmt = None
        self.lineno = False

    def _open(self):
        encoding = CRLogHandler.encoding
        errors = CRLogHandler.err_to_read
        f_obj = FileInput(self.path, openhook=hook_encoded(encoding, errors))
        self.file_obj = f_obj

        return self.file_obj

    def __enter__(self):
        return self._open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug("Exception has been handled")
        self.file_obj.close()

    @property
    def get_cr_id_from_filename(self):
        # example: DTV03036540-2020-10-28-015510-bsp_common_common.sh_90001-kernel.log

        cr_id_pattern = self.cr_id_pattern
        m_obj = re.search(cr_id_pattern, self.base_filename)
        if m_obj:
            self.cr_id = m_obj.group(0)

        return self.cr_id

    @property
    def is_from_autolog(self):
        cr_id = self.get_cr_id_from_filename
        crid_suffix = cr_id + '-'
        autolog_fmt = r"^\d{4}-\d{2}-\d{2}-\d{6}-.*\.(?:log)$"

        if cr_id:
            new_fn = re.sub(crid_suffix, "", self.base_filename)
            is_autolog = re.search(autolog_fmt, new_fn)
            if is_autolog:
                self.is_autolog = True

        return self.is_autolog