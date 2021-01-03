#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
from multiprocessing import Manager

manager = Manager()
SharedFileContent = manager.dict()

print(os.getpid())
