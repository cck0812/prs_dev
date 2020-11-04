#!/usr/bin/python
# -*- coding: utf-8 -*-
from marshmallow import Schema, fields, INCLUDE


class PatternValuesSchema(Schema):
    lineno = fields.Integer()
    machine_time = fields.Integer()
    value = fields.Str()
    result = fields.Str()

    class Meta:
        unknown = INCLUDE


class IssueCategorySchema(Schema):
    function = fields.Str()
    module = fields.Str()
    project = fields.Str()
    platform = fields.Str()
    action = fields.Str()
    pattern_info = fields.List(
        fields.Nested(PatternValuesSchema)
    )

    class Meta:
        unknown = INCLUDE


class ResultSchema(Schema):
    timestamp = fields.Date()
    cr_id = fields.Str(required=True)
    filename = fields.Str()
    filepath = fields.Str()
    filesize = fields.Integer()
    is_from_auto = fields.Bool()
    log_format = fields.Str()
    extracted_pattern = fields.List(
        fields.Nested(IssueCategorySchema)
    )


def main():
    pass


if __name__ == '__main__':
    main()