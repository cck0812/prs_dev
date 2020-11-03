#!/usr/bin/python
# -*- coding: utf-8 -*-
import json
import logging


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


def main():
    result = ResultCollector()
    basic_info = dict(
        timestamp="1604044294",
        cr_id="DTV03037343",
        filename="filename",
        filepath="/path/to/file",
        filesize=1685233,
        is_from_auto=True,
        log_format="autolog"
    )    
    result.update_basic_info(**basic_info)

    extracted_pattern_info = dict(
        common=[],
        other_issue_category=[]
    )
    result.update_extracted_pattern(**extracted_pattern_info)
    print(result.results)

if __name__ == '__main__':
    main()