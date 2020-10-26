#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from modules.models import LogInformation


class CRLogFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = datetime.now()
        self.filename = None
        self.file_path = None
        self.file_size = None

    def on_created(self, event):
        if not event.is_directory:
            self.file_path = event.src_path
            self.filename = os.path.abspath(os.path.basename(self.file_path))
            self.file_size = os.path.getsize(self.file_path)

        file_info = LogInformation(filename=self.filename, file_path=self.file_path, file_size = self.file_size)
        file_info.save()

        print(f'event type: {event.event_type}  path : {event.src_path} file size {self.file_size}')

    def on_modified(self, event):
        print(f'event type: {event.event_type}  path : {event.src_path}')


def get_file_ext(filename):
    # Get the file extension
    file_ext = filename.split(".",1)[1]
    return file_ext


def main():
    event_handler = CRLogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path='.', recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()

