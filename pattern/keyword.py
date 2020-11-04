#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
import logging
# dev
import sys
SCRIPT_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR)))
# dev
from configs.setup_settings import CFGSettings


class Keyword():
    CONFIG_SET = ["pattern_meta", "pattern_keyword"]

    def __init__(self, conf):
        self.logger = logging.getLogger(__name__)
        if isinstance(conf, dict):
            self.conf = {cs:conf[cs] for cs in Keyword.CONFIG_SET}
        else:
            raise ValueError("conf needs to be a dictionary type")

    def compile_all_search_strings(self):
        ics = self.conf['pattern_keyword']['issue_categories']
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


def main():
    path = 'H:\mtk_project\prs_dev\example\DTV03036540-2020-10-28-015510-bsp_common_common.sh_90001-kernel.log'
    conf_obj = CFGSettings()                    
    conf_obj.load_conf(conf_folder=True)
    conf = vars(conf_obj)
    parser = Keyword(conf)
    
    from utils.handler import CRLogHandler
    from utils.result_collector import FinalResultCollector

    result = FinalResultCollector()
    with CRLogHandler(path, result) as cr_obj:
        parser.get_pattern_value(cr_obj)



if __name__ == "__main__":
    main()