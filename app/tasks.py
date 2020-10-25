from celery import shared_task
import time
from utils.test import TESTMD

@shared_task
def celery_task(counter):
    email = "hassanzadeh.sd@gmail.com"
    time.sleep(2)
    return '{} Done!'.format(TESTMD)
