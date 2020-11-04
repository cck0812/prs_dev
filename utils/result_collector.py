#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import logging
from utils.result_schema import ResultSchema, IssueCategorySchema, PatternValuesSchema


class ResultCollector():
    def __init__(self):
        self._results = {}
        self.extracted_pattern = None
        self.issue_category = None

    def update_basic_info(self, **kwargs):
        return self._results.update(kwargs)

    def update_extracted_pattern(self, key='extracted_pattern', **kwargs):
        if self._results.get(key) == None:
            self.update_basic_info(**{key:[]})        
        self.extracted_pattern = self._results.get(key)
        self.extracted_pattern.append(kwargs)

        return self.update_basic_info(**{key:self.extracted_pattern})

    def update_issue_category(self):
        pass

    @property
    def results(self):
        return self._results

    def output_file(self, filename):
        pass


class FinalResultCollector():
    def __init__(self, **kwargs):
        self.extracted_pattern = None
        self.__dict__.update(kwargs)


class IssueCategoryCollector():
    def __init__(self, **kwargs):
        self.pattern_info = None
        self.__dict__.update(kwargs)


class PatternValueCollector():
    def __init__(self, attrs):
        self.__dict__.update(attrs)


def main():
    pattern_value_info_1 = dict(
        lineno=1,
        timestamp= 710.285797,
        value="value_1",
        result="result_1"
    )
    pattern_value_info_2 = dict(
        lineno=2,
        timestamp= 710.285797,
        value="value_2",
        result="result_2"
    )
    pattern_values_infos = [pattern_value_info_1, pattern_value_info_2]
    pv_objs = (PatternValueCollector(pv) for pv in pattern_values_infos) # a Generator

    
    basic_info = dict(
        timestamp="1604044294",
        cr_id="DTV03037343",
        filename="filename",
        filepath="/path/to/file",
        filesize=1685233,
        is_from_auto=True,
        log_format="autolog"
    )    
    result = FinalResultCollector(**basic_info)
    if result.extracted_pattern == None:
        extracted_pattern_info = dict(
            common=[],
            other_issue_category=[]
        )
        result.extracted_pattern = [{k:v} for k, v in extracted_pattern_info.items()]


if __name__ == '__main__':
    main()