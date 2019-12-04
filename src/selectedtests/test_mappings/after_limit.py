from git import Commit
from typing import Optional
from datetime import datetime

from evergreen.api import Version\

class AfterLimit(object):
    """Represents the point in time at which to start analyzing commits of an evergreen project."""

    def __init__(self, after_date: Optional[datetime] = None, after_commit_sha: Optional[str] = None):
        self.after_date = after_date
        self.after_commit_sha = after_commit_sha

    def check_commit_after_limit(self, commit: Commit):
        if self.after_date:
            if commit.committed_datetime < self.after_date:
                return True
        else:
            if commit.hexsha == self.after_commit_sha:
                return True
        return False

    def check_version_after_limit(self, version: Version):
        if self.after_date:
            if version.create_time < self.after_date:
                return True
        else:
            if commit.hexsha == self.after_commit_sha:
                return True
        return False
