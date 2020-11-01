import os
import time
from celery import shared_task


@shared_task
def celery_task(file_path):
    time.sleep(2)
    return '{} Done!, size: {}'.format(file_path, os.path.getsize(file_path))