from django.shortcuts import HttpResponse
from app.tasks import celery_task


def celery_view(request):
    for counter in range(3):
        celery_task.delay(counter)
    return HttpResponse("FINISH PAGE LOAD")
