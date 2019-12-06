"""Test Mappings class to create test mappings."""
import structlog
import os.path

from collections import defaultdict, namedtuple
from typing import Pattern
from git import Repo
from tempfile import TemporaryDirectory
from evergreen.api import EvergreenApi
from evergreen.manifest import ManifestModule
from selectedtests.git_helper import init_repo, modified_files_for_commit
from selectedtests.evergreen_helper import get_evg_project

LOGGER = structlog.get_logger(__name__)


def generate_test_mappings(
    evg_api: EvergreenApi,
    evergreen_project: str,
    after_project_commit: str,
    source_re: Pattern,
    test_re: Pattern,
    module_name: str = None,
    after_module_commit: str = None,
    module_source_re: Pattern = None,
    module_test_re: Pattern = None,
):
    """
    Generate test mappings for an evergreen project and its associated module if module is provided.

    :param evg_api: An instance of the evg_api client
    :param evergreen_project: The name of the evergreen project to analyze.
    :param after_project_commit: The commit at which to start analyzing commits of the project.
    :param source_re: Regex pattern to match changed source files against.
    :param test_re: Regex pattern to match changed test files against.
    :param module_name: The name of the module to analyze.
    :param after_module_commit: The commit at which to start analyzing commits of the module.
    :param module_source_re: Regex pattern to match changed module source files against.
    :param module_test_re: Regex pattern to match changed module test files against.
    :return: A list of test mappings for the evergreen project and (optionally) its module
    """
    log = LOGGER.bind(
        project=evergreen_project,
        module=module_name,
        after_project_commit=after_project_commit,
        after_module_commit=after_module_commit,
    )
    log.info("Starting to generate test mappings")
    project_last_commit_sha_analyzed = None
    module_last_commit_sha_analyzed = None
    TestMappingsResult = namedtuple(
        "ProjectMappingsResult",
        [
            "test_mappings_list",
            "project_last_commit_sha_analyzed",
            "module_last_commit_sha_analyzed",
        ],
    )
    with TemporaryDirectory() as temp_dir:
        test_mappings_list, project_last_commit_sha_analyzed = generate_project_test_mappings(
            evg_api, evergreen_project, temp_dir, source_re, test_re, after_project_commit
        )

        if module_name:
            module_test_mappings_list, module_last_commit_sha_analyzed = generate_module_test_mappings(
                evg_api,
                evergreen_project,
                module_name,
                temp_dir,
                module_source_re,
                module_test_re,
                after_module_commit,
            )
            test_mappings_list.extend(module_test_mappings_list)
    log.info("Generated test mappings list", test_mappings_length=len(test_mappings_list))
    test_mappings_result = TestMappingsResult(
        test_mappings_list=test_mappings_list,
        project_last_commit_sha_analyzed=project_last_commit_sha_analyzed,
        module_last_commit_sha_analyzed=module_last_commit_sha_analyzed,
    )
    return test_mappings_result


def generate_project_test_mappings(
    evg_api: EvergreenApi,
    evergreen_project: str,
    temp_dir: TemporaryDirectory,
    source_re: Pattern,
    test_re: Pattern,
    after_commit: str,
):
    """
    Generate test mappings for an evergreen project.

    :param evg_api: An instance of the evg_api client
    :param evergreen_project: The name of the evergreen project to analyze.
    :param temp_dir: The place where to clone the repo to.
    :param source_re: Regex pattern to match changed source files against.
    :param test_re: Regex pattern to match changed test files against.
    :param after_commit: The commit at which to start analyzing commits of the project's git repo.
    :return: A list of test mappings for the evergreen project
    """
    evg_project = get_evg_project(evg_api, evergreen_project)
    project_repo = init_repo(
        temp_dir, evg_project.repo_name, evg_project.branch_name, evg_project.owner_name
    )
    project_test_mappings, project_last_commit_sha_analyzed = TestMappings.create_mappings(
        project_repo, source_re, test_re, after_commit, evergreen_project, evg_project.branch_name
    )
    return project_test_mappings.get_mappings(), project_last_commit_sha_analyzed


def generate_module_test_mappings(
    evg_api: EvergreenApi,
    evergreen_project: str,
    module_name: str,
    temp_dir: TemporaryDirectory,
    module_source_re: Pattern,
    module_test_re: Pattern,
    after_commit: str,
):
    """
    Generate test mappings for an evergreen module.

    :param evg_api: An instance of the evg_api client
    :param evergreen_project: The name of the evergreen project that the module belongs to.
    :param module_name: The name of the module to analyze.
    :param temp_dir: The place where to clone the repo to.
    :param module_source_re: Regex pattern to match changed module source files against.
    :param module_test_re: Regex pattern to match changed module test files against.
    :param after_commit: The commit at which to start analyzing commits of the module's git repo.
    :return: A list of test mappings for the evergreen module
    """
    module = _get_module(evg_api, evergreen_project, module_name)
    module_repo = init_repo(temp_dir, module.repo, module.branch, module.owner)
    module_test_mappings, module_last_commit_sha_analyzed = TestMappings.create_mappings(
        module_repo,
        module_source_re,
        module_test_re,
        after_commit,
        evergreen_project,
        module.branch,
    )
    return module_test_mappings.get_mappings(), module_last_commit_sha_analyzed


def _get_module(evg_api: EvergreenApi, project: str, module_repo: str) -> ManifestModule:
    """
    Fetch the module associated with an Evergreen project.

    :param evg_api: An instance of the evg_api client
    :param project: The name of the evergreen project to analyze.
    :param module_repo: Name of the module to analyze
    :return: evg_api client instance of the module
    """
    version_iterator = evg_api.versions_by_project(project)
    recent_version = next(version_iterator)
    modules = recent_version.get_manifest().modules
    return modules.get(module_repo)


class TestMappings(object):
    """Represents and creates the test mappings for an evergreen project."""

    def __init__(
        self,
        file_intersection: defaultdict,
        file_count_map: defaultdict,
        project: str,
        repo_name: str,
        branch: str,
    ):
        """
        Create a TestMappings object.

        :param file_intersection: Map of how files intersect.
        :param file_count_map: Map of how many times files where seen.
        :param project: The name of the evergreen project to analyze.
        :param repo_name: The name of the git repo used for the evergreen project.
        :param branch: The branch of the git repo used for the evergreen project.
        """
        self._file_intersection = file_intersection
        self._file_count_map = file_count_map
        self._project = project
        self._repo_name = repo_name
        self._branch = branch
        self._test_mappings = None

    @classmethod
    def create_mappings(
        cls,
        repo: Repo,
        source_re: Pattern,
        test_re: Pattern,
        after_commit: str,
        project: str,
        branch: str,
    ):
        """
        Create the test mappings for a git repo.

        :param repo: The repo that contains the source code for the evergreen project.
        :param source_re: Regex pattern to match changed source files against.
        :param test_re: Regex pattern to match changed test files against.
        :param after_commit: The commit at which to start analyzing commits of the repo.
        :param project: The name of the evergreen project to analyze.
        :param branch: The branch of the git repo used for the evergreen project.
        :return: An instance of the test mappings class
        """
        file_intersection = defaultdict(lambda: defaultdict(int))
        file_count = defaultdict(int)
        last_commit_sha_analyzed = None

        for commit in repo.iter_commits(repo.head.commit):
            LOGGER.debug(
                "Investigating commit",
                summary=commit.message.splitlines()[0],
                ts=commit.committed_datetime,
                id=commit.hexsha,
            )

            if commit.hexsha == after_commit:
                break

            last_commit_sha_analyzed = commit.hexsha
            tests_changed = set()
            src_changed = set()
            for path in modified_files_for_commit(commit, LOGGER):
                LOGGER.debug("found change", path=path)

                if test_re.match(path):
                    tests_changed.add(path)
                elif source_re.match(path):
                    src_changed.add(path)

            for src in src_changed:
                file_count[src] += 1
                for test in tests_changed:
                    file_intersection[src][test] += 1

        repo_name = os.path.basename(repo.working_dir)
        return (
            TestMappings(file_intersection, file_count, project, repo_name, branch),
            last_commit_sha_analyzed,
        )

    def get_mappings(self):
        """
        Get a transformed version of test mappings to the test mapping object.

        :return: Transformed test mappings
        """
        if not self._test_mappings:
            self._test_mappings = self._transform_mappings()
        return self._test_mappings

    def _transform_mappings(self):
        test_mappings = []
        for source_file, test_file_count_dict in self._file_intersection.items():
            test_files = [
                {"name": test_file, "test_file_seen_count": test_file_seen_count}
                for test_file, test_file_seen_count in test_file_count_dict.items()
            ]
            test_mapping = {
                "source_file": source_file,
                "project": self._project,
                "repo": self._repo_name,
                "branch": self._branch,
                "source_file_seen_count": self._file_count_map[source_file],
                "test_files": test_files,
            }
            test_mappings.append(test_mapping)
        return test_mappings
