#!/usr/bin/python
# -*- coding: utf-8 -*-
from marshmallow import pprint
from marshmallow import Schema, fields


class ResultSchema(Schema):
    timestamp = fields.Date()
    cr_id = fields.Str()
    filename = fields.Str()
    filepath = fields.Str()
    filesize = fields.Integer()
    is_from_auto = fields.Bool()
    log_format = fields.Str()
    extracted_pattern = fields.Nested()
    

class IssueCategorySchema(Schema):
    