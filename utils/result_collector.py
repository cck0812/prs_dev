#!/usr/bin/python
# -*- coding: utf-8 -*-
import json


class ResultCollector():
    def __init__(self):
        results = None
        extracted_pattern = None
        issue_categories = None

    def update_basic_info(self, **kwargs):
        if self.results == None:
            self.results = dict()
            
        return self.results.update(**kwargs)

    def update_extracted_pattern(self, **kwargs):
        if not self.extracted_pattern:
            self.extracted_pattern = []
            self.results.update(dict(extracted_pattern=[]))

    @property
    def results(self):
        return self.results