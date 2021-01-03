#!/usr/bin/python
# -*- coding: utf-8 -*-
import hashlib
import itertools
import json
import logging
import os
from datetime import datetime
from pathlib import Path

from celery import Task, group, shared_task
from django.utils import timezone
from pattern.pattern_handler import PatternHandler
from utils.handler import CRLogHandler
from utils.shared_mem import SharedFileContent, manager
from utils.tools import import_func

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    _db = None

    def db(self, django_model=None):
        if django_model is None:
            return
        elif self._db is None:
            model_path = f"modules.models.{django_model}"
            model = import_func(model_path)
            queryset = model.objects
            self._db = queryset

        return self._db


@shared_task
def dispatcher(file_path):
    collection = CRLogHandler(file_path).collect()
    SharedFileContent.update(collection)
    file_name = list(collection.keys())[0]
    hashed_fp = hashlib.md5(file_path.encode("utf-8")).hexdigest()

    return hashed_fp


@shared_task
def fetch_pattern(collection, shm_key, shm_chunk_key, parser_idx):
    parsers_list = PatternHandler().get_parsers_list()
    parser = parsers_list[parser_idx]

    file_content = SharedFileContent[shm_key][shm_chunk_key]["file_content"]
    base_idx = SharedFileContent[shm_key][shm_chunk_key]["base_idx"]
    queue = SharedFileContent[shm_key][parser.name]

    ts = datetime.now().strftime("%F %T")
    mt_conf = PatternHandler().ts_conf

    logger.debug(f"pattern: {getattr(parser, parser.name)} is ready for parsing.")
    try:
        result_list = parser.get_pattern_value(
            file_content=file_content,
            base_idx=base_idx,
            timestamp=ts,
            machine_time_conf=mt_conf,
            **collection,
        )
        logger.debug(f"pattern: {getattr(parser, parser.name)} was done.")

        if not result_list == []:
            queue.put(result_list)
            path = Path(PatternHandler().output)
            if path.exists():
                temp_dir = path.joinpath("temp")
                if not temp_dir.exists():
                    temp_dir.mkdir()

                file_string = "{}_{}_{}_{}".format(
                    shm_chunk_key, parser.function, parser.name, parser_idx
                )
                md5 = hashlib.md5(file_string.encode("utf-8")).hexdigest()
                temp_name = f"{md5}.temp"
            else:
                raise FileNotFoundError(
                    f"{path} doesn't exist, please assign a valid directory path."
                )

            with temp_dir.joinpath(temp_name).open("w", encoding="utf-8") as f:
                newline = ""
                for r in result_list:
                    r = json.dumps(r)
                    f.write(newline + r)
                    newline = "\n"

        return True

    except Exception as err:
        template = "An exception of type {0!r} occurred. Arguments:{1!r}"
        message = template.format(type(err).__name__, err.args)
        logger.exception(message)

        return False

    # finally:
    #     sl.shm.close()
    #     logger.info(f"Worker ID: {parser_idx} closed {sl.shm.name} successfully.")
    #     return


@shared_task(ignore_result=True)
def merge_file():
    # SharedFileContent.clear()  # Clean up the shared dictionary.

    path = Path(PatternHandler().output)
    assert path.exists(), f"{path} doesn't exist, please assign a valid directory path."

    if path.joinpath("temp").exists():
        temp_files = list(path.joinpath("temp").glob("*.temp"))
    else:
        logger.info("There's no file need to be processed.")
        return

    if temp_files != []:
        date = datetime.strftime(datetime.now(), "%Y%m%d")
        issue_file = path.joinpath(f"pattern_result-{date}.issue")

        with issue_file.open("at", encoding="utf-8") as w:

            for tem in temp_files:
                with tem.open("rt", encoding="utf-8") as r:
                    result = r.read()

                    newline = ""
                    if issue_file.stat().st_size != 0:
                        newline = "\n"
                    w.write(newline + result)
                    newline = "\n"

                try:
                    tem.unlink()
                except OSError as e:  # if failed, report it back to the user
                    logger.error("Error: {} - {}.".format(e.filename, e.strerror))


@shared_task
def add(x, y):
    return x + y


@shared_task
def update_shm(dict):
    print(os.getpid())
    SharedFileContent.update(dict)


@shared_task
def get_shm(dict):
    print(os.getpid())
    return SharedFileContent.items()


@shared_task
def send(x, token=None):
    if token:
        sl = ShareableList(name=token)
        print(sl)


def process_data(django_model=None):
    assert django_model is not None, "Please give one django model to update."

    queryset = django_model.objects
    if not queryset.filter(is_done=False).exists():
        logger.info("There's no file updated.")
        return
    else:
        parsers_list = PatternHandler().get_parsers_list()
        logger.info("Prepared the parsers.")

        objs = queryset.order_by("created_time").filter(is_done=False)
        logger.info("Starting to parse files.")

        result_set = []
        for obj in objs:
            fp = obj.file_path
            with CRLogHandler(fp) as cr_log:
                cr_log.update_queue_to_shm()  # Update queues into shared content.
                chunks = cr_log.file
                collection = cr_log.collect()
                shm_key = list(collection.keys())[0]
                base_idx = 0

                for idx, chunk in enumerate(chunks):
                    shm_chunk_key = f"{shm_key}_{idx}"
                    file_content = list(chunk)
                    line_counts = len(file_content)
                    SharedFileContent[shm_key].update(
                        {
                            shm_chunk_key: {
                                "file_content": file_content,
                                "base_idx": base_idx,
                            }
                        }
                    )

                    res = group(
                        fetch_pattern.s(collection, shm_key, shm_chunk_key, idx)
                        for idx in range(len(parsers_list))
                    )()
                    result_set.append((obj, res))
                    base_idx += line_counts

        logger.info(f"{len(objs)* len(parsers_list)} parser jobs were dispatched !!")

        update_objs = []
        while result_set:
            res = result_set[0]
            obj, group_res = res

            if group_res.ready():
                logger.debug(f"Task of {obj.filename} was parsed successfully.")
                obj.is_done = True
                obj.parsed_time = timezone.now()
                update_objs.append(obj)

                result_set.pop(0)
            else:
                # Maybe it can try to use asyncio solution for optimizing.
                time.sleep(0.3)
                continue

        try:
            queryset.bulk_update(update_objs, ["is_done", "parsed_time"])
            logger.info(f"There're {len(update_objs)} files have been updated.")
        except Exception as err:
            logger.error(f"The updated process was failed ! {err.args}")
        finally:
            connections.close_all()
            logger.debug("Dispatch merge file task.")
            merge_file.apply_async()


# @task_postrun.connect
# def task_postrun_handler(
#     task=None,
#     args=None,
#     state=None,
#     **kwargs,
# ):
#     if task.name == "modules.tasks.dispatcher":
#         file_path, model_name = args
#         queryset = task.db(model_name)
#         uk = hashlib.md5(file_path.encode("utf-8")).hexdigest()

#         record = queryset.get(unique_id=uk)
#         record.is_done = True
#         record.parsed_time = timezone.now()

#         record.save()
#         logger.info(f"{file_path} has been parsed.")
#         connections.close_all()
