#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import json
import codecs
import logging
import fileinput
from configs.setup_settings import CFGSettings
from utils.handler import CRLogHandler


class FetchPatternInfo(CRLogHandler):
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "configs",
                                "pattern_meta.json")
    FILENAME_NO_EXT = os.path.splitext(os.path.basename(CONFIG_PATH))[0] # ["pattern_meta", ".json"]

    def __init__(self, path):
        super().__init__(path)
        self.logger = logging.getLogger(__name__)
        self.conf = None

    def _setup_settings(self):
        conf = CFGSettings()
        attr_keys = vars(conf).keys()
        conf_path = FetchPatternInfo.CONFIG_PATH
        conf_key = FetchPatternInfo.FILENAME_NO_EXT

        if conf_key not in attr_keys:
            conf.load_conf(conf_path=conf_path)
        self.conf = conf.conf_key

        return self.conf

    def get_pattern_info(self):
        if self.file_obj not is None:
            f_obj = self.file_obj

        pattern_str = re.compile()
        for line in f_obj:
            


    @property
    def get_file_length(self):
        if self.file_obj:
            self.file_len = sum(1 for line in self.file_obj)

        return self.file_len
