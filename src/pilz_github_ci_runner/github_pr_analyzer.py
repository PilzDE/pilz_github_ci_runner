# Copyright (c) 2021 Pilz GmbH & Co. KG
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import github
from collections import namedtuple
from github.PullRequest import PullRequest

ENABLE_TEXT = "- [ ] Perform hardware tests"
ALLOW_TEXT = "Allow hw-tests up to commit "


class PullRequestValidator(PullRequest):
    def validate(self, allowed_users, test_bot_account):
        self.is_internal = self._is_internal()
        self.head_commit_is_allowed = self._head_commit_is_allowed_by_comment(
            allowed_users)
        self.requests_tests = self._description_contain_enable_string()
        self.head_is_untested = not self._tested(test_bot_account)

    def is_valid(self):
        return self.state == "open" \
            and self.requests_tests \
            and self._is_allowed()

    def _is_allowed(self):
        return self.is_internal or self.head_commit_is_allowed

    def _description_contain_enable_string(self):
        if self.body.find(ENABLE_TEXT) != -1:
            return True
        return False

    def _is_internal(self):
        return self.base.repo.full_name == self.head.repo.full_name

    def _head_commit_is_allowed_by_comment(self, allowed_users):
        for c in self.get_issue_comments():
            if c.user.login in allowed_users and c.body.find(ALLOW_TEXT + self.head.sha) != -1:
                return True

    def _tested(self, test_bot_account):
        for c in self.get_issue_comments():
            if c.user.login == test_bot_account \
               and c.body.startswith("Finished test of %s" % self.head.sha):
                return True
        return False

    def status_report(self, long=False) -> str:
        title = "PR #%s %s" % (self.number, self.title30())
        enabled = "enabled" if self.requests_tests else "disabled"
        origin = "Changes are internal" if self.is_internal else \
                 "External changes are accepted" if self.head_commit_is_allowed else \
                 "Has unaccepted external changes"
        tested = "(Untested)" if self.head_is_untested else "(No untested changes)"
        return "%s Testing %s. %s. %s" % (title, enabled, origin, tested) if long else "%s %s" % (title, tested)

    def title30(self):
        return (self.title[:28].rstrip() + ".." if len(self.title) > 30 else self.title).ljust(30)


def get_testable_pull_requests(repo_handler):
    testable_pull_requests = []
    print("%s\nSearching for PRs to test.\n" % (">"*50))
    for pr in repo_handler.repo.get_pulls():
        pr.__class__ = PullRequestValidator
        pr.validate(repo_handler.allowed_users, repo_handler.test_bot_account)
        print(pr.status_report(long=True))
        if pr.is_valid():
            testable_pull_requests.append(pr)
    print("<"*50)
    return testable_pull_requests


def create_repo_handler(token, repo_name, allowed_users):
    gh = github.Github(token)
    test_bot_account = gh.get_user().login
    repo = gh.get_repo(repo_name)
    return namedtuple("RepoHandler", ["repo", "allowed_users", "test_bot_account"])(repo, allowed_users, test_bot_account)
