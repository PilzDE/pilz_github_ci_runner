from github.PullRequest import PullRequest

ENABLE_TEXT = "- [ ] Perform hardware tests"
ALLOW_TEXT = "Allow hw-tests up to commit "


class PullRequestValidator(PullRequest):
    def validate(self, allowed_users, test_bot_account):
        self.is_internal = self._is_internal()
        self.head_commit_is_allowed = self._head_commit_is_allowed_by_comment(
            allowed_users)
        self.requests_tests = self._description_contain_enable_string()
        self.head_is_untested = self._not_tested_yet(test_bot_account)

    def is_valid(self):
        return self.state == "open" \
            and self.requests_tests \
            and self._is_allowed() \
            and self.head_is_untested

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

    def _not_tested_yet(self, test_bot_account):
        for c in self.get_issue_comments():
            if c.user.login == test_bot_account \
               and c.body.startswith("Finished test of %s" % self.head.sha):
                return False
        return True

    def status(self) -> str:
        s = "PR #%s " % self.number
        if not self.requests_tests:
            s += "is not enabled for testing."
        elif not self.is_internal and not self.head_commit_is_allowed:
            s += "is an external PR. The head commit needs to be accepted."
        elif not self.head_is_untested:
            s += "has no untested changes."
        else:
            s += "is enabled and ready for testing."
        return s


def get_testable_pull_requests(repo, allowed_users, test_bot_account):
    testable_pull_requests = []
    print("%s\nSearching for PRs to test.\n" % (">"*50))
    for pr in repo.get_pulls():
        pr.__class__ = PullRequestValidator
        pr.validate(allowed_users, test_bot_account)
        print(pr.status())
        if pr.is_valid():
            testable_pull_requests.append(pr)
    print("<"*50)
    return testable_pull_requests
