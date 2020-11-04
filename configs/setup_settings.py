#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import glob
import json


class CFGSettings():
    __single = None
    CONFIG_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "configs")

    def __new__(cls):
        if not CFGSettings.__single:
            CFGSettings.__single = object.__new__(cls)
            
        return CFGSettings.__single
        
    def load_conf(self, conf=None, conf_folder=None):
        # pre-checks
        if not (conf or conf_folder):
            raise AttributeError("please assign either a config as object or a config file folder.")

        conf_paths = glob.iglob(os.path.join(CFGSettings.CONFIG_FOLDER, '*.json'))
        for conf_path in conf_paths:
            if conf_path.endswith("logging.json") or conf_path.endswith("splunk_schema.json"): # dev
                continue
            if conf_path and isinstance(conf_path, str):
                if not os.path.isfile(conf_path):
                    raise FileExistsError(f"'{conf_path}' isn't file type.")

                # read config files
                import codecs

                with codecs.open(conf_path, "rb", encoding="utf-8") as f:
                    fn = os.path.splitext(os.path.basename(conf_path))[0]
                    conf = json.load(f)

                    setattr(self, fn, conf)


def main():
    conf = CFGSettings()                    
    conf.load_conf(conf_folder=True)
    print(vars(conf))


if __name__ == "__main__":
    main()                    