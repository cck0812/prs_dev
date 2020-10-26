#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.db.models import Model
from django.db.models import DateTimeField, \
                             CharField, \
                             IntegerField


class LogInformation(Model):
    created_time = DateTimeField(auto_now_add=True)
    last_modified_time = DateTimeField(auto_now=True)
    filename = CharField(max_length=200)
    file_path = CharField(max_length=200)
    file_size = IntegerField(default=0)

    class Meta:
        db_table = "log_information"
