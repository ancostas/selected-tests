import json

from pymongo.collection import Collection


class TaskConfig:
    def __init__(
        self,
        most_recent_version_analyzed,
        source_file_regex,
        build_variant_regex,
        module,
        module_source_file_regex,
    ):
        self.most_recent_version_analyzed = most_recent_version_analyzed
        self.source_file_regex = source_file_regex
        self.build_variant_regex = build_variant_regex
        self.module = module
        self.module_source_file_regex = module_source_file_regex

    @classmethod
    def from_json(cls, json):
        return cls(
            json.get("most_recent_version_analyzed", None),
            json.get("source_file_regex", None),
            json.get("build_variant_regex", None),
            json.get("module", None),
            json.get("module_source_file_regex", None),
        )

    def update(
        self,
        most_recent_version_analyzed,
        source_file_regex,
        build_variant_regex,
        module,
        module_source_file_regex,
    ):
        self.most_recent_version_analyzed = most_recent_version_analyzed
        self.source_file_regex = source_file_regex
        self.build_variant_regex = build_variant_regex
        self.module = module
        self.module_source_file_regex = module_source_file_regex

    def update_most_recent_version_analyzed(self, most_recent_version_analyzed):
        self.most_recent_version_analyzed = most_recent_version_analyzed


class TestConfig:
    def __init__(
        self,
        most_recent_project_commit_analyzed,
        source_file_regex,
        test_file_regex,
        module,
        most_recent_module_commit_analyzed,
        module_source_file_regex,
        module_test_file_regex,
    ):
        self.most_recent_project_commit_analyzed = most_recent_project_commit_analyzed
        self.source_file_regex = source_file_regex
        self.test_file_regex = test_file_regex
        self.module = module
        self.most_recent_module_commit_analyzed = most_recent_module_commit_analyzed
        self.module_source_file_regex = module_source_file_regex
        self.module_test_file_regex = module_test_file_regex

    @classmethod
    def from_json(cls, json):
        return cls(
            json.get("most_recent_project_commit_analyzed", None),
            json.get("source_file_regex", None),
            json.get("test_file_regex", None),
            json.get("module", None),
            json.get("most_recent_module_commit_analyzed", None),
            json.get("module_source_file_regex", None),
            json.get("module_test_file_regex", None),
        )

    def update(
        self,
        most_recent_project_commit_analyzed,
        source_file_regex,
        test_file_regex,
        module,
        most_recent_module_commit_analyzed,
        module_source_file_regex,
        module_test_file_regex,
    ):
        self.most_recent_project_commit_analyzed = most_recent_project_commit_analyzed
        self.source_file_regex = source_file_regex
        self.test_file_regex = test_file_regex
        self.module = module
        self.most_recent_module_commit_analyzed = most_recent_module_commit_analyzed
        self.module_source_file_regex = module_source_file_regex
        self.module_test_file_regex = module_test_file_regex

    def update_most_recent_commits_analyzed(
        self, most_recent_project_commit_analyzed, most_recent_module_commit_analyzed
    ):
        self.most_recent_project_commit_analyzed = most_recent_project_commit_analyzed
        self.most_recent_module_commit_analyzed = most_recent_module_commit_analyzed


class ProjectConfig:
    def __init__(self, project, task_config: TaskConfig = None, test_config: TestConfig = None):
        self.project = project
        self.task_config = task_config
        self.test_config = test_config

    @classmethod
    def get(cls, collection: Collection, project):
        data = collection.find({"project": project})
        if data:
            return cls(
                project,
                TaskConfig.from_json(data.get("task_config")),
                TestConfig.from_json(data.get("test_config")),
            )
        return cls(project)

    def save(self, collection):
        self.collection.update(
            {"project": self.project},
            {
                "task_config": json.dumps(self.task_config.__dict__),
                "test_config": json.dumps(self.test_config.__dict__),
            },
            True,
        )
