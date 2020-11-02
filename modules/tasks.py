#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import time
import json
import logging
from celery import shared_task
from pattern.common import FetchPatternInfo
from pattern.keyword import Keyword


logger = logging.getLogger(__name__)

@shared_task
def celery_task(file_path):
    try:
        pattern_handler = FetchPatternInfo(file_path)
        pattern_obj = Keyword()
        if not pattern_obj.conf:
            pattern_obj._setup_settings()
        gen_obj = pattern_obj.get_pattern_value(pattern_handler._open())
        
        # if not len(gen_obj):
        #     logger.debug("Generator is empty, please check the process")
        #     raise ValueError
        with open('.\\dest_folder\\test.issue', 'w', encoding='utf-8') as f:
            for d in gen_obj:
                dstr = str(d)
                f.write(dstr)
                f.write('\n')

    except:
        pass

    return f"Done !"