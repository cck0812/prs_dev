#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import json


class CFGSettings():
    __single = None

    def __new__(cls):
        if not CFGSettings.__single:
            CFGSettings.__single = object.__new__(cls)
            
        return CFGSettings.__single
        
    def load_conf(self, conf=None, conf_path=None):
        # pre-checks
        if not (conf or conf_path):
            raise AttributeError("please assign either a config as object or a config file path.")

        if conf_path and isinstance(conf_path, str):
            if not os.path.isfile(conf_path):
                raise FileExistsError(f"'{conf_path}' isn't file type.")

            # read config file
            import codecs
            with codecs.open(conf_path, "rb", encoding="utf-8") as f:
                fn = os.path.basename(conf_path)
                fn_list = os.path.splitext(fn)
                fn_noExt = fn_list[0]
                conf = json.load(f)

        setattr(self, fn_noExt, conf)