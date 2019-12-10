"""Evergreen.py helper."""
from datetime import datetime
from typing import Optional

from evergreen.api import EvergreenApi, Project
from evergreen.manifest import ManifestModule
from tempfile import TemporaryDirectory

from selectedtests.git_helper import init_repo


def get_evg_project(evg_api: EvergreenApi, project: str) -> Optional[Project]:
    """
    Fetch an Evergreen project's info from the Evergreen API.

    :param evg_api: An instance of the evg_api client
    :param project: The name of the evergreen project to analyze.
    :return: evg_api client instance of the project
    """
    for evergreen_project in evg_api.all_projects():
        if evergreen_project.identifier == project:
            return evergreen_project
    return None


def get_evg_module_for_project(
    evg_api: EvergreenApi, project: str, module_repo: str
) -> ManifestModule:
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


def get_project_commit_on_date(evg_api, evergreen_project, after_date):
    project_commit = None
    with TemporaryDirectory() as temp_dir:
        evg_project = get_evg_project(evg_api, evergreen_project)
        project_repo = init_repo(
            temp_dir, evg_project.repo_name, evg_project.branch_name, evg_project.owner_name
        )

        for commit in project_repo.iter_commits(project_repo.head.commit):
            if commit.committed_datetime < after_date:
                break
            project_commit = commit.hexsha

    return project_commit


def get_module_commit_on_date(evg_api, evergreen_project, after_date, module_name):
    module_commit = None
    with TemporaryDirectory() as temp_dir:
        module = get_evg_module_for_project(evg_api, evergreen_project, module_name)
        module_repo = init_repo(temp_dir, module.repo, module.branch, module.owner)

        for commit in module_repo.iter_commits(module_repo.head.commit):
            if commit.committed_datetime < after_date:
                break
            module_commit = commit.hexsha

    return module_commit


def get_version_on_date(evg_api, evergreen_project, after_date):
    project_versions = evg_api.versions_by_project_time_window(
        evergreen_project, datetime.utcnow(), after_date
    )
    after_version = None
    for version in project_versions:
        after_version = version.version_id
    return after_version
