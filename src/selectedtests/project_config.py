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


class ProjectConfig:
    def __init__(self, project, task_config: TaskConfig = None, test_config: TestConfig = None):
        self.project = project
        self.task_config = task_config
        self.test_config = test_config

    @classmethod
    def get(cls, collection: Collection, project):
        data = collection.find({"project": project})
        if data:
            task_config = TaskConfig(
                data.get("task_config.most_recent_version_analyzed", None),
                data.get("task_config.source_file_regex", None),
                data.get("task_config.build_variant_regex", None),
                data.get("task_config.module", None),
                data.get("task_config.module_source_file_regex", None),
            )
            test_config = TestConfig(
                data.get("task_config.most_recent_project_commit_analyzed", None),
                data.get("task_config.source_file_regex", None),
                data.get("task_config.test_file_regex", None),
                data.get("task_config.module", None),
                data.get("task_config.most_recent_module_commit_analyzed", None),
                data.get("task_config.module_source_file_regex", None),
                data.get("task_config.module_test_file_regex", None),
            )
            return cls(project, task_config, test_config)
        return cls(project)

    def save(self, collection):
        self.collection.update(
            {"project": self.project},
            {
                "task_config.most_recent_version_analyzed": self.task_config.most_recent_version_analyzed,
                "task_config.source_file_regex": self.task_config.source_file_regex,
                "task_config.build_variant_regex": self.task_config.build_variant_regex,
                "task_config.module": self.task_config.module,
                "task_config.module_source_file_regex": self.task_config.module_source_file_regex,
                "test_config.most_recent_project_commit_analyzed": self.test_config.most_recent_project_commit_analyzed,
                "test_config.source_file_regex": self.test_config.source_file_regex,
                "test_config.test_file_regex": self.test_config.test_file_regex,
                "test_config.module": self.test_config.module,
                "test_config.most_recent_module_commit_analyzed": self.test_config.most_recent_module_commit_analyzed,
                "test_config.module_source_file_regex": self.test_config.module_source_file_regex,
                "test_config.module_test_file_regex": self.test_config.module_test_file_regex,
            },
            True,
        )

    def update_task_config(
        self,
        most_recent_version_analyzed,
        source_file_regex,
        build_variant_regex,
        module,
        module_source_file_regex,
    ):
        self.task_config.most_recent_version_analyzed = most_recent_version_analyzed
        self.task_config.source_file_regex = source_file_regex
        self.task_config.build_variant_regex = build_variant_regex
        self.task_config.module = module
        self.task_config.module_source_file_regex = module_source_file_regex

    def update_test_config(
        self,
        most_recent_project_commit_analyzed,
        source_file_regex,
        test_file_regex,
        module,
        most_recent_module_commit_analyzed,
        module_source_file_regex,
        module_test_file_regex,
    ):
        self.test_config.most_recent_project_commit_analyzed = most_recent_project_commit_analyzed
        self.test_config.source_file_regex = source_file_regex
        self.test_config.test_file_regex = test_file_regex
        self.test_config.module = module
        self.test_config.most_recent_module_commit_analyzed = most_recent_module_commit_analyzed
        self.test_config.module_source_file_regex = module_source_file_regex
        self.test_config.module_test_file_regex = module_test_file_regex
