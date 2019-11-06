"""Functions for processing project test mapping work items."""
import re
import structlog

from selectedtests.work_items.project_test_mapping_work_item import ProjectTestMappingWorkItem
from datetime import datetime
from evergreen.api import EvergreenApi
from selectedtests.datasource.mongo_wrapper import MongoWrapper
from selectedtests.test_mappings.mappings import generate_test_mappings

LOGGER = structlog.get_logger()


def _clear_in_progress_work(collection):
    """
    Clear the start time of all in progress work items.

    This is done at the start of a run to retry any work items that may not have completed
    during a previous run.

    :param collection: Collection to act on.
    """
    collection.update_many({"end_time": None}, {"$set": {"start_time": None}})


def _run_create_test_mappings(
    evg_api: EvergreenApi,
    mongo: MongoWrapper,
    work_item: ProjectTestMappingWorkItem,
    start_date: datetime,
    end_date: datetime,
) -> bool:
    log = LOGGER.bind(project=work_item.project)
    log.info("starting test mapping processing")
    source_re = re.compile(work_item.source_file_regex)
    test_re = re.compile(work_item.test_file_regex)
    module_source_re = None
    module_test_re = None
    if work_item.module:
        module_source_re = re.compile(work_item.module_source_file_regex)
        module_test_re = re.compile(work_item.module_test_file_regex)

    test_mappings_list = generate_test_mappings(
        evg_api,
        work_item.project,
        source_re,
        test_re,
        start_date,
        end_date,
        work_item.module,
        module_source_re,
        module_test_re,
    )
    if test_mappings_list:
        mongo.test_mappings().insert_many(test_mappings_list)
    log.info("Finished test mapping work item processing")
    return True


def process_queued_work_items(
    evg_api: EvergreenApi, mongo: MongoWrapper, start_date: datetime, end_date: datetime
):
    _clear_in_progress_work(mongo.test_mappings_queue())
    try:
        while True:
            out_of_work = _process_one_work_item(evg_api, mongo, start_date, end_date)
            if out_of_work:
                break
    except:  # noqa: E722
        LOGGER.warning("Unexpected exception processing project test mapping", exc_info=1)


def _process_one_work_item(
    evg_api: EvergreenApi, mongo: MongoWrapper, start_date: datetime, end_date: datetime
) -> bool:
    work_item = ProjectTestMappingWorkItem.next(mongo.test_mappings_queue())
    if not work_item:
        return True

    log = LOGGER.bind(project=work_item.project)
    log.info("Starting test mapping work item processing")
    if _run_create_test_mappings(evg_api, mongo, work_item, start_date, end_date):
        work_item.complete(mongo.test_mappings_queue())

    return False
