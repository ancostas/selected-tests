import git
import os
import pytz
import pdb
import pytest

from datetime import datetime, time, timedelta
from tempfile import TemporaryDirectory
from unittest.mock import patch, MagicMock

import selectedtests.evergreen_helper as under_test

NS = "selectedtests.evergreen_helper"


def ns(relative_name):
    """Return a full name from a name relative to the tested module"s name space."""
    return NS + "." + relative_name


class TestGetEvgProject:
    def test_project_exists(self):
        evg_api_mock = MagicMock()
        evg_api_mock.all_projects.return_value = [
            MagicMock(identifier=f"project_{i}", owner_name=f"owner_{i}") for i in range(3)
        ]
        project_name = "project_1"

        project = under_test.get_evg_project(evg_api_mock, project_name)
        assert project.identifier == project_name
        assert project.owner_name == "owner_1"

    def test_project_does_not_exist(self):
        evg_api_mock = MagicMock()
        evg_api_mock.all_projects.return_value = [
            MagicMock(identifier=f"project_{i}", owner_name=f"owner_{i}") for i in range(3)
        ]
        project_name = "project_4"

        project = under_test.get_evg_project(evg_api_mock, project_name)
        assert not project


class TestGetEvgModuleForProject:
    def test_module_exists(self, evg_versions_with_manifest):
        mock_evg_api = MagicMock()
        mock_evg_api.versions_by_project.return_value = evg_versions_with_manifest
        module = under_test.get_evg_module_for_project(
            mock_evg_api, "mongodb-mongo-master", "my-module"
        )

        assert module.repo == "module-repo"
        assert module.branch == "module-branch"
        assert module.owner == "module-owner"

    def test_module_does_not_exist(self, evg_versions_with_manifest):
        mock_evg_api = MagicMock()

        version_mock = MagicMock()
        version_mock.get_manifest.return_value = MagicMock(modules={"not-my-module": MagicMock()})
        versions = [version_mock]
        mock_evg_api.versions_by_project.return_value = (v for v in versions)

        module = under_test.get_evg_module_for_project(
            mock_evg_api, "mongodb-mongo-master", "my-module"
        )

        assert not module


@pytest.fixture(scope="function")
def repo_with_interval_commits(monkeypatch):
    def _repo(tmpdir):
        repo = git.Repo.init(tmpdir)

        # commit something four days ago
        four_days_ago = str(datetime.combine(datetime.now() - timedelta(days=4), time()))
        monkeypatch.setenv("GIT_AUTHOR_DATE", four_days_ago)
        monkeypatch.setenv("GIT_COMMITTER_DATE", four_days_ago)
        repo.index.commit("initial commit -- no files changed")

        # commit something two days ago
        two_days_ago = str(datetime.combine(datetime.now() - timedelta(days=2), time()))
        monkeypatch.setenv("GIT_AUTHOR_DATE", two_days_ago)
        monkeypatch.setenv("GIT_COMMITTER_DATE", two_days_ago)
        some_file = os.path.join(tmpdir, "some-file")
        open(some_file, "wb").close()
        repo.index.add([some_file])
        commit_two_days_ago = repo.index.commit("add some file")

        # commit something today
        now = str(datetime.combine(datetime.now(), time()))
        monkeypatch.setenv("GIT_AUTHOR_DATE", now)
        monkeypatch.setenv("GIT_COMMITTER_DATE", now)
        another_file = os.path.join(tmpdir, "another-file")
        open(another_file, "wb").close()
        repo.index.add([another_file])
        repo.index.commit("add another file")
        return repo, commit_two_days_ago

    return _repo


class TestGetProjectCommitOnDate:
    @patch(ns("get_evg_project"))
    @patch(ns("init_repo"))
    def test_returns_project_commit_that_happened_before_date(
        self,
        init_repo_mock,
        get_evg_project_mock,
        repo_with_interval_commits
    ):
        evg_api = MagicMock()
        project = "valid-evergreen-project"
        get_evg_project_mock.return_value = MagicMock(identifier=project)
        with TemporaryDirectory() as tmpdir:

            init_repo_mock.return_value, commit_two_days_ago = repo_with_interval_commits(tmpdir)

            three_days_ago = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=3)
            commit_on_date = under_test.get_project_commit_on_date(tmpdir, evg_api, project, three_days_ago)

            assert commit_on_date == commit_two_days_ago.hexsha


class TestGetModuleCommitOnDate:
    @patch(ns("get_evg_project"))
    @patch(ns("init_repo"))
    def test_returns_module_commit_that_happened_before_date(
        self,
        init_repo_mock,
        get_evg_module_for_project,
        repo_with_interval_commits
    ):
        evg_api = MagicMock()
        get_evg_module_for_project.return_value = MagicMock(repo="repo", branch="branch", owner="owner")
        with TemporaryDirectory() as tmpdir:

            init_repo_mock.return_value, commit_two_days_ago = repo_with_interval_commits(tmpdir)

            three_days_ago = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(days=3)
            commit_on_date = under_test.get_project_commit_on_date(tmpdir, evg_api, "my-module", three_days_ago)

            assert commit_on_date == commit_two_days_ago.hexsha
