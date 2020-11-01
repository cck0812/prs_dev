#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import os
from datetime import datetime
from django.shortcuts import HttpResponse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from modules.models import LogInformation
from modules.tasks import celery_task


class CRLogFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_modified = datetime.now()
        self.filename = None
        self.file_path = None
        self.file_size = None

    def on_created(self, event):
        if not event.is_directory:
            self.file_path = event.src_path
            self.filename = os.path.basename(os.path.abspath(self.file_path))
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


def main(request):
    event_handler = CRLogFileHandler()
    observer = Observer()
    observer.schedule(event_handler, path='/app/prs_dev/src_folder', recursive=False)
    observer.start()
    count = 0

    try:
        while count < 10:
            count += 1
            time.sleep(1)
    finally:
        observer.stop()
    observer.join()

    time.sleep(10)
    queryset = LogInformation.objects.all()
    results = list(queryset.order_by('created_time').filter(is_done=False).values())
    results_count = len(results)
    for object in results:
        id = object['id']
        fp = object['file_path']
        celery_task.delay(fp)
        queryset.filter(id=id).update(is_done=True)

    return HttpResponse(f"Page Loaded, processed count: {results_count}")


if __name__ == "__main__":
    main()