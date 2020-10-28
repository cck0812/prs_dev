#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import codecs
import logging


class CRLogHandler():
    def __init__(self, path, mode='r', encoding='utf-8', cr_id_pattern=r'^(?:DTV)\d+'):
        self.logger = logging.getLogger(__name__)
        self.base_filename = os.path.basename(path)
        self.path = path
        self.mode = mode
        self.encoding = encoding
        self.file_obj = codecs.open(path, mode=mode, encoding=encoding)
        self.file_len = None
        self.cr_id = None 
        self.cr_id_pattern = cr_id_pattern
        self.is_autolog = False
        self.logfmt = None
        self.lineno = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.debug("Exception has been handled")
        self.file_obj.close()

    @property
    def get_file_length(self):
        if self.file_obj:
            self.file_len = sum(1 for line in self.file_obj)

        return self.file_len

    @property
    def get_cr_id_from_filename(self, cr_id_pattern=None):
        # example: DTV03036540-2020-10-28-015510-bsp_common_common.sh_90001-kernel.log
        if cr_id_pattern is None:
            cr_id_pattern = self.cr_id_pattern

        m_obj = re.search(cr_id_pattern, self.base_filename)
        if m_obj:
            self.cr_id = m_obj.group(0)

        return self.cr_id

    @property
    def is_from_autolog(self, cr_id_pattern=None):
        if cr_id_pattern is None:
            cr_id_pattern = self.cr_id_pattern
        cr_id = self.get_cr_id_from_filename(cr_id_pattern)
        prefix_crid = cr_id + '-'
        autolog_fmt = r"^\d{4}-\d{2}-\d{2}-\d{6}-.*\.(?:log)$"

        if cr_id:
            new_fn = re.sub(prefix_crid, "", self.base_filename)
            is_autolog = re.match(autolog_fmt, new_fn)
        self.is_autolog = is_autolog

        return self.is_autolog

    @property
    def get_log_format(self):
        pass

    @property
    def show_line_number(self):
        pass