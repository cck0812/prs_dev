#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import logging
from configs.setup_settings import CFGSettings

class Keyword():
    CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                "configs",
                                "pattern_keyword.json")
    FILENAME_NO_EXT = os.path.splitext(os.path.basename(CONFIG_PATH))[0] # ["pattern_keyword", ".json"]

    def __init__(self):
        self.conf = None
        self.logger = logging.getLogger(__name__)

    def _setup_settings(self):
        conf = CFGSettings()
        attr_keys = vars(conf).keys()
        conf_path = Keyword.CONFIG_PATH
        conf_key = Keyword.FILENAME_NO_EXT

        if conf_key not in attr_keys:
            conf.load_conf(conf_path=conf_path)
        self.conf = getattr(conf, conf_key)

        return self.conf

    def compile_all_search_strings(self):
        if self.conf is None:
            self._setup_settings()

        ics = self.conf['issue_categories']
        for ic in ics:
            ic_list = ics[ic]
            for ic_index, pcs in enumerate(ic_list): # pcs: pattern_categories
                pc = pcs['pattern_categories']
                compile_group = [[ic, ic_index, p, pc[p]] for p in pc]

        compiled_group = []
        while len(compile_group):
            compile_list = compile_group.pop(0)
            if compile_list[2].startswith('keyword'):
                func = self.get_keyword_compile

            elif compile_list[2].startswith('key_value'):
                func = self.get_key_value_compile

            map_obj = map(func, compile_list[3])
            compiled_strs = list(map_obj)
            compile_list[3] = compiled_strs
            compiled_group.append(compile_list)

        return compiled_group

    @staticmethod
    def get_keyword_compile(element):
        return re.compile(element)

    @staticmethod
    def get_key_value_compile(element):
        key = re.escape(element['key'])
        prefix = re.escape(element['prefix'])
        suffix = re.escape(element['suffix'])

        return re.compile(f"(?P<key>{key})(?:{prefix})(?P<value>.*?)(?:{suffix})")

    def get_pattern_value(self, line):
        compiled_strs = self.compile_search_strings()
        for c_str in compiled_strs:
            match_obj = c_str.search(line)
            if match_obj:
                match_dict = dict(
                                value=match_obj.group(1),
                                results=line
                            )

                yield match_dict

"""
for line in log:
    for re_c in re_c_list:
        m_obj = re_c.search(line)
        if m_obj:
            print(f"Line: {log.lineno()}, Value: {m_obj.group(1)}, Results: {line}")
"""  