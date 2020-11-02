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
        compile_group = []
        for ic in ics:
            ic_list = ics[ic]
            for ic_index, pcs_dict in enumerate(ic_list): 
                pcs = pcs_dict['pattern_categories'] # pcs: pattern_categories
                for p in pcs:
                    compile_group.append([ic, ic_index, p, pcs[p]])

        compiled_group = []
        """
        data structure: compile_group: nested list
        [
            [
                issus_category, index, pattern_category, [search patterns]
            ],
            [
                ...another pattern_category
            ]
        ]
        """
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

    def get_pattern_value(self, file_obj):
        compiled_str_lists = self.compile_all_search_strings()
        for line in file_obj:
            for compiled_str_list in compiled_str_lists:
                ic, ic_idx, pc, compiled_strs = compiled_str_list

                for c_str in compiled_strs:
                    match = c_str.search(line)
                    if match:
                        match_dict = dict(
                                        issue_category=ic,
                                        ic_index=ic_idx,
                                        pattern_category=pc,
                                        lineno=file_obj.lineno(),
                                        value=match.group(),
                                        results=line
                                    )

                        yield match_dict