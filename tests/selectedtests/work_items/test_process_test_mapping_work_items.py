from unittest.mock import MagicMock, patch
from selectedtests.test_mappings.create_test_mappings import TestMappingsResult
import selectedtests.work_items.process_test_mapping_work_items as under_test


NS = "selectedtests.work_items.process_test_mapping_work_items"


def ns(relative_name):  # pylint: disable=invalid-name
    """Return a full name from a name relative to the test module"s name space."""
    return NS + "." + relative_name


class TestProcessQueuedTestMappingWorkItems:
    @patch(ns("_process_one_test_mapping_work_item"))
    @patch(ns("_generate_test_mapping_work_items"))
    def test_analyze_runs_while_work_available(
        self, mock_gen_test_map_work_items, mock_process_one_test_mapping_work_item
    ):
        n_work_items = 3
        mock_gen_test_map_work_items.return_value = [MagicMock() for _ in range(n_work_items)]
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_test_mapping_work_items(evg_api_mock, mongo_mock, after_date=None)

        assert n_work_items == mock_process_one_test_mapping_work_item.call_count

    @patch(ns("_process_one_test_mapping_work_item"))
    def test_analyze_does_not_throw_exceptions(self, mock_process_one_test_mapping_work_item):
        mock_process_one_test_mapping_work_item.side_effect = ValueError("Unexpected Exception")
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test.process_queued_test_mapping_work_items(evg_api_mock, mongo_mock, after_date=None)


class TestProcessOneTestMappingWorkItem:
    @patch(ns("_run_create_test_mappings"))
    def test_work_items_completed_successfully_are_marked_complete(
        self, run_create_test_mappings_mock
    ):
        work_item_mock = MagicMock()
        run_create_test_mappings_mock.return_value = True
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test._process_one_test_mapping_work_item(
            work_item_mock, evg_api_mock, mongo_mock, after_date=None
        )

        work_item_mock.complete.assert_called_once()

    @patch(ns("_run_create_test_mappings"))
    def test_work_items_completed_unsuccessfully_are_marked_not_complete(
        self, run_create_test_mappings_mock
    ):
        work_item_mock = MagicMock()
        run_create_test_mappings_mock.return_value = False
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()

        under_test._process_one_test_mapping_work_item(
            work_item_mock, evg_api_mock, mongo_mock, after_date=None
        )

        work_item_mock.complete.assert_not_called()


class TestRunCreateTestMappings:
    @patch(ns("generate_test_mappings"))
    @patch(ns("get_project_commit_on_date"))
    def test_mappings_are_created(self, get_project_commit_on_date_mock, generate_test_mappings_mock):
        get_project_commit_on_date_mock.return_value = "commit-sha-six-months-ago"
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        logger_mock = MagicMock()
        generate_test_mappings_mock.return_value = TestMappingsResult(
            test_mappings_list=["mock-mapping"],
            project_last_commit_sha_analyzed="last-project-sha-analyzed",
            module_last_commit_sha_analyzed="last-module-sha-analyzed",
        )
        work_item_mock = MagicMock(source_file_regex="src", test_file_regex="test", module=None)

        under_test._run_create_test_mappings(
            evg_api_mock, mongo_mock, work_item_mock, after_date=None, log=logger_mock
        )

        mongo_mock.test_mappings.return_value.insert_many.assert_called_once_with(["mock-mapping"])

    @patch(ns("generate_test_mappings"))
    @patch(ns("get_project_commit_on_date"))
    def test_no_mappings_are_created(self, get_project_commit_on_date_mock, generate_test_mappings_mock):
        get_project_commit_on_date_mock.return_value = "commit-sha-six-months-ago"
        evg_api_mock = MagicMock()
        mongo_mock = MagicMock()
        logger_mock = MagicMock()
        generate_test_mappings_mock.return_value = TestMappingsResult(
            test_mappings_list=[],
            project_last_commit_sha_analyzed=None,
            module_last_commit_sha_analyzed=None,
        )
        mongo_mock.test_mappings.return_value.insert_many.side_effect = TypeError(
            "documents must be a non-empty list"
        )
        work_item_mock = MagicMock(source_file_regex="src", test_file_regex="test", module=None)

        under_test._run_create_test_mappings(
            evg_api_mock, mongo_mock, work_item_mock, after_date=None, log=logger_mock
        )

        mongo_mock.test_mappings.return_value.insert_many.assert_not_called()
