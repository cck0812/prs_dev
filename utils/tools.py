#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import json


def load_conf(conf=None, conf_path=None):
    # Pre-checks
    if not (conf or conf_path):
        raise AttributeError("Please assign either a config as object or a config file path.")

    if conf_path and isinstance(conf_path, str):
        if not os.path.isfile(conf_path):
            raise FileExistsError(f"'{conf_path}' isn't file type.")

        # Read Config file
        import codecs
        with codecs.open(conf_path, "rb", encoding="utf-8") as f:
            conf = json.load(f)

    return conf