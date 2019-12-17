from pymongo.collection import Collection


class ProjectConfig:
    def __init__(self, project, collection: Collection):
        self.project = project
        self.collection = collection

    def update(self, params: dict, upsert: bool = False):
        collection.update({"project": self.project}, {"$set": params}, upsert=upsert)

    def create_task_config(
        self,
        most_recent_version_analyzed,
        source_file_regex,
        build_variant_regex,
        module,
        module_source_file_regex,
    ):
        self.collection.update(
            {"project": self.project},
            {
                "task_config.most_recent_version_analyzed": most_recent_version_analyzed,
                "task_config.source_file_regex": source_file_regex,
                "task_config.build_variant_regex": build_variant_regex,
                "task_config.module": module,
                "task_config.module_source_file_regex": module_source_file_regex,
            },
            True,
        )

    def create_test_config(
        self,
        most_recent_project_commit_analyzed,
        source_file_regex,
        test_file_regex,
        module,
        most_recent_module_commit_analyzed,
        module_source_file_regex,
        module_test_file_regex,
    ):
        self.collection.update(
            {"project": self.project},
            {
                "test_config.most_recent_project_commit_analyzed": most_recent_project_commit_analyzed,
                "test_config.source_file_regex": source_file_regex,
                "test_config.test_file_regex": test_file_regex,
                "test_config.module": module,
                "test_config.most_recent_module_commit_analyzed": most_recent_module_commit_analyzed,
                "test_config.module_source_file_regex": module_source_file_regex,
                "test_config.module_test_file_regex": module_test_file_regex,
            },
            True,
        )

    def update_most_recent_version_analyzed(self, most_recent_version_analyzed):
        self.collection.update(
            {"project": self.project},
            {"task_config.most_recent_version_analyzed": most_recent_version_analyzed},
        )

    def update_most_recent_commits_analyzed(
        self, most_recent_project_commit_analyzed, most_recent_module_commit_analyzed
    ):
        self.collection.update(
            {"project": self.project},
            {
                "test_config.most_recent_project_commit_analyzed": most_recent_project_commit_analyzed,
                "test_config.most_recent_module_commit_analyzed": most_recent_module_commit_analyzed,
            },
        )
