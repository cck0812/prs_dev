#!/usr/bin/python
# -*- coding: utf-8 -*-
import copy
import logging
import os
import re
import sys
import time
from abc import ABCMeta, abstractmethod
from datetime import datetime
from functools import reduce

from marshmallow import ValidationError
from nested_lookup import nested_lookup

SCRIPT_DIR = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR)))
from configs.setup_settings import CFGSettings
from marshmallow import Schema, fields, post_load
from utils.tools import singleton


class ParserMeta(metaclass=ABCMeta):
    #  pattern_bsp_audio, pattern_platform_csp, pattern_bsp_video
    CONFIG_SET = ["pattern_test"]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.parsers = None
        self.conf = CFGSettings().load_conf(conf_folder=True)
        self.conf = {cs: getattr(self.conf, cs) for cs in self.CONFIG_SET}

        self.conf = load_pattern_conf(self.conf, self.name)
        # That means there's no relevant settings in config files.
        if not any(self.conf):
            self.logger.info(
                f"There's no {self.name} settings in {self.CONFIG_SET} configs"
            )
            return
        elif not self.is_compiled:
            self.compile_strings()

            if self.is_compiled:
                self.instantiate_parser()

                if self.parsers is None:
                    self.logger.info(
                        f"There's no available parser for {self.name} to use."
                    )

    def instantiate_parser(self):
        if self.parsers is None:
            schema = PatternConfig(many=True)
            try:
                parsers = schema.load(self.conf)
            except ValidationError as err:
                self.logger.error(err.messages)
                return

            self.parsers = parsers

    @abstractmethod
    def compile_strings(self):
        pass

    # @abstractmethod
    # def get_pattern_values(self, line):
    #     pass


@singleton(refresh_parser=True)
class KeywordParser(ParserMeta):
    def __init__(self):
        self.name = "keyword"
        self.is_compiled = False
        super().__init__()

    def compile_strings(self):
        for val in self.conf:
            pattern = val.get(self.name)
            pattern_compiled = re.compile("|".join(pattern))
            pattern = list(map(lambda srch: re.compile(srch), pattern))
            val.update({self.name: pattern_compiled})
        self.is_compiled = True

        return self.is_compiled


@singleton(refresh_parser=True)
class KeyValueParser(ParserMeta):
    def __init__(self):
        self.name = "key_value"
        self.is_compiled = False
        super().__init__()

    def compile_strings(self):
        for val in self.conf:
            pattern = val.get(self.name)
            operation = {
                d.get("key", None): {
                    "operator": d.get("operator"),
                    "operand": d.get("operand"),
                }
                for d in pattern
                if ("operator" in d) or ("operand" in d)
            }
            if operation:
                val.update(dict(operation=operation))

            pattern = list(
                map(lambda srch: self.get_key_value_compile(**srch), pattern)
            )
            # pattern_combined = re.compile("|".join(pattern))
            val.update({self.name: pattern})
        self.is_compiled = True

        return self.is_compiled

    @staticmethod
    def get_key_value_compile(**kwargs):
        if kwargs["key"] is None or kwargs["value"] is None:
            return
        else:
            keyorder = ["key_prefix", "key", "prefix", "value", "suffix"]
            kv_conf = {key: val for key, val in kwargs.items() if key in keyorder}
            kv_conf = dict(sorted(kv_conf.items(), key=lambda i: keyorder.index(i[0])))

            kv_pattern = [
                f"({val})" if key in ("key", "value") else f"(?:{val})"
                for key, val in kv_conf.items()
            ]

            return re.compile("".join(kv_pattern))


@singleton(refresh_parser=True)
class SequenceParser(ParserMeta):
    def __init__(self):
        self.name = "sequence"
        self.is_compiled = False
        super().__init__()

    def compile_strings(self):
        for val in self.conf:
            pattern = val.get(self.name)

            sequence_idx = {}
            for idx, pat in enumerate(pattern):
                sequence_idx[idx] = {s: i for i, s in enumerate(pat)}

            sequence_status = [[0] * len(val) for val in sequence_idx.values()]
            sequence_order = [1] * len(sequence_idx)

            pattern = ["({})".format("|".join(group)) for group in pattern]
            pattern_compiled = re.compile("|".join(pattern))

            val.update(
                {
                    self.name: pattern_compiled,
                    "sequence_idx": sequence_idx,
                    "sequence_status": sequence_status,
                    "sequence_order": sequence_order,
                }
            )
        self.is_compiled = True

        return self.is_compiled


class PatternCollector:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
        self.logger = logging.getLogger(__name__)

    def key_value_pattern(self, **kwargs):
        file_content = kwargs["file_content"]
        result_list = kwargs["result_list"]
        ts = kwargs["timestamp"]
        mt_conf = kwargs["machine_time_conf"]
        cr_id = kwargs["cr_id"]
        fn = kwargs["filename"]

        self.logger.debug(f"Starting to parse {len(file_content)} lines.")
        for srch in self.key_value:
            for idx, line in enumerate(file_content):
                match_obj = srch.search(line)

                if match_obj:
                    # If the setting of key-value has any expression,
                    # then need to be computed
                    key = match_obj.group(1)
                    value = match_obj.group(2)

                    result_dict = dict(
                        timestamp=ts,
                        CR_ID=cr_id,
                        issue_category=self.issue_category,
                        ic_idx=self.ic_idx,
                        function=self.function,
                        filename=fn,
                        pattern_category=self.name,
                        lineno=idx + 1,
                        machine_time=self.get_log_timestamp(line, mt_conf),
                        key=key,
                        value=value,
                        raw=line.rstrip("\n"),
                    )

                    if hasattr(self, "operation"):
                        if key in self.operation:
                            exp = self.operation.get(key)
                            exp.update(dict(value=value))

                            if self.eval_expression(exp):
                                result_list.append(result_dict)
                                continue
                            else:
                                continue

                    result_list.append(result_dict)

        return result_list

    def keyword_pattern(self, **kwargs):
        file_content = kwargs["file_content"]
        base_idx = kwargs["base_idx"]
        result_list = kwargs["result_list"]
        ts = kwargs["timestamp"]
        mt_conf = kwargs["machine_time_conf"]
        cr_id = kwargs["cr_id"]
        fn = kwargs["filename"]

        self.logger.debug(f"Starting to parse {len(file_content)} lines.")
        srch = self.keyword
        for idx, line in enumerate(file_content):
            match_obj = srch.search(line)

            if match_obj:
                m_group = match_obj.groups()  # The groups method return a tuple.
                value = m_group[0] if m_group else match_obj.group()
                result_dict = dict(
                    timestamp=ts,
                    CR_ID=cr_id,
                    issue_category=self.issue_category,
                    ic_idx=self.ic_idx,
                    function=self.function,
                    filename=fn,
                    pattern_category=self.name,
                    lineno=base_idx + idx + 1,
                    machine_time=self.get_log_timestamp(line, mt_conf),
                    value=value,
                    raw=line.rstrip("\n"),
                )
                result_list.append(result_dict)

        return result_list

    def sequence_pattern(self, **kwargs):
        file_content = kwargs["file_content"]
        result_list = kwargs["result_list"]
        ts = kwargs["timestamp"]
        mt_conf = kwargs["machine_time_conf"]
        cr_id = kwargs["cr_id"]
        fn = kwargs["filename"]
        line_counts = kwargs["line_counts"]

        self.logger.debug(f"Starting to parse {len(file_content)} lines.")
        srch = self.sequence
        for idx, line in enumerate(file_content):
            match_obj = srch.search(line)
            lineno = base_idx + idx + 1

            if match_obj:
                value = match_obj.group()
                seq_idx = match_obj.lastindex - 1
                srch_idx = reduce(dict.get, [seq_idx, value], self.sequence_idx)
                last_srch_idx = len(self.sequence_idx.get(seq_idx)) - 1

                if srch_idx == last_srch_idx:
                    self.sequence_status[seq_idx][srch_idx] = 1

                    for i, val in enumerate(self.sequence_status[seq_idx]):
                        if val == 0:
                            missing_key = [
                                key
                                for key, val in self.sequence_idx[seq_idx].items()
                                if val == i
                            ][0]
                            result_list.append(
                                dict(
                                    timestamp=ts,
                                    CR_ID=cr_id,
                                    issue_category=self.issue_category,
                                    ic_idx=self.ic_idx,
                                    function=self.function,
                                    filename=fn,
                                    pattern_category=self.name,
                                    seq_id=seq_idx,
                                    seq_order=self.sequence_order[seq_idx],
                                    srch_idx=i,
                                    lineno=None,
                                    value=missing_key,
                                    raw=None,
                                )
                            )

                    result_list.append(
                        dict(
                            timestamp=ts,
                            CR_ID=cr_id,
                            issue_category=self.issue_category,
                            ic_idx=self.ic_idx,
                            function=self.function,
                            filename=fn,
                            pattern_category=self.name,
                            seq_id=seq_idx,
                            seq_order=self.sequence_order[seq_idx],
                            srch_idx=srch_idx,
                            lineno=lineno,
                            machine_time=self.get_log_timestamp(line, mt_conf),
                            value=value,
                            raw=line.rstrip("\n"),
                        )
                    )

                    self.sequence_order[seq_idx] += 1
                    self.sequence_status[seq_idx] = [0] * len(
                        self.sequence_status[seq_idx]
                    )

                else:
                    if any(self.sequence_status[seq_idx][srch_idx + 1 :]):
                        for i, val in enumerate(self.sequence_status[seq_idx]):
                            if val == 0:
                                missing_key = [
                                    key
                                    for key, val in self.sequence_idx[seq_idx].items()
                                    if val == i
                                ][0]
                                result_list.append(
                                    dict(
                                        timestamp=ts,
                                        CR_ID=cr_id,
                                        issue_category=self.issue_category,
                                        ic_idx=self.ic_idx,
                                        function=self.function,
                                        filename=fn,
                                        pattern_category=self.name,
                                        seq_id=seq_idx,
                                        seq_order=self.sequence_order[seq_idx],
                                        srch_idx=i,
                                        lineno=None,
                                        value=missing_key,
                                        raw=None,
                                    )
                                )

                        self.sequence_order[seq_idx] += 1
                        self.sequence_status[seq_idx] = [0] * len(
                            self.sequence_status[seq_idx]
                        )

                    self.sequence_status[seq_idx][srch_idx] = 1
                    result_list.append(
                        dict(
                            timestamp=ts,
                            CR_ID=cr_id,
                            issue_category=self.issue_category,
                            ic_idx=self.ic_idx,
                            function=self.function,
                            filename=fn,
                            pattern_category=self.name,
                            seq_id=seq_idx,
                            seq_order=self.sequence_order[seq_idx],
                            srch_idx=srch_idx,
                            lineno=lineno,
                            machine_time=self.get_log_timestamp(line, mt_conf),
                            value=value,
                            raw=line.rstrip("\n"),
                        )
                    )
            if lineno == line_counts:
                if not any(map(lambda seq: any(seq), self.sequence_status)):
                    return result_list
                else:
                    for seq_idx, status in enumerate(self.sequence_status):
                        if not any(status):
                            continue
                        else:
                            for i, val in enumerate(status):
                                if val == 0:
                                    missing_key = [
                                        key
                                        for key, val in self.sequence_idx[
                                            seq_idx
                                        ].items()
                                        if val == i
                                    ][0]

                                    result_list.append(
                                        dict(
                                            timestamp=ts,
                                            CR_ID=cr_id,
                                            issue_category=self.issue_category,
                                            ic_idx=self.ic_idx,
                                            function=self.function,
                                            filename=fn,
                                            pattern_category=self.name,
                                            seq_id=seq_idx,
                                            seq_order=self.sequence_order[seq_idx],
                                            srch_idx=i,
                                            lineno=None,
                                            value=missing_key,
                                            raw=None,
                                        )
                                    )

        return result_list

    @staticmethod
    def eval_expression(exp):
        return eval("{value} {operator} {operand}".format(**exp))

    def get_pattern_value(self, *args, **kwargs):
        # Using suffix: _pattern to catch different parser to parse.
        return getattr(self, self.name + "_pattern")(*args, **kwargs)

    def get_log_timestamp(self, line, ts_conf):
        mt_pattern = ts_conf.get("pattern")
        pos = ts_conf.get("pos")
        endpos = ts_conf.get("endpos")
        group = ts_conf.get("group")
        for pat in mt_pattern:
            srch_str = re.compile(pat)
            match = srch_str.search(line, pos=pos, endpos=endpos)
            if match:
                return match.group(group)


class PatternConfig(Schema):
    conf_name = fields.Str()
    issue_category = fields.Str()
    ic_idx = fields.Integer()
    name = fields.Str()
    function = fields.Str()
    operation = fields.Field()
    keyword = fields.Field()

    # parse pattern use for-loop is faster than regex union.
    key_value = fields.List(fields.Field())

    sequence = fields.Field()
    sequence_idx = fields.Field()
    sequence_status = fields.Field()
    sequence_order = fields.List(fields.Integer())

    @post_load
    def make_pattern(self, data, **kwargs):
        return PatternCollector(**data)


def load_pattern_conf(confs, pattern_category):
    pattern_confs = []
    for conf_fn, conf in confs.items():
        ics_conf = conf.get("issue_categories")
        if not ics_conf:
            continue

        for key, vals in ics_conf.items():
            # pre-check the pattern category in list of the issue category or not.
            pre_check = any(
                val.get("pattern_categories", {}).get(pattern_category) for val in vals
            )
            if not pre_check:
                continue

            for idx, val in enumerate(vals):
                pcs = val["pattern_categories"]
                func = val["function"]
                pc = pcs.get(pattern_category, None)
                if pc is None:
                    continue

                pattern_conf = dict(
                    conf_name=conf_fn,
                    issue_category=key,
                    function=func,
                    ic_idx=idx,
                    name=pattern_category,
                )
                pattern_conf.update({pattern_category: pc})
                pattern_confs.append(pattern_conf)

    return pattern_confs


def main():
    from pattern.pattern_handler import PatternHandler
    from utils.handler import CRLogHandler

    path = "C:\\Users\\vend_John_Chung001\\Desktop\\Work_Progress\\TV_Issue_Compass\\Pattern_Regnition\\Log_example\\BSP_Video\\wiki\\20000101001716-video_common.sh-kernel.log"

    seq = SequenceParser()
    collection = CRLogHandler(path).collect()
    timestamp = datetime.strftime(datetime.now(), "%F %T")
    mt_conf = PatternHandler().ts_conf
    start_time = time.time()
    parser = seq.parsers[0]
    result_list = parser.get_pattern_value(
        timestamp=timestamp,
        machine_time_conf=mt_conf,
        **collection["20000101001716-video_common.sh-kernel.log"],
    )
    end_time = time.time()
    print("total time taken this loop: ", end_time - start_time)
    for i in result_list:
        print(i)


if __name__ == "__main__":
    import cProfile

    cProfile.run("main()", "statics")
