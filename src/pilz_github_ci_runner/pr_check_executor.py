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
import time
from collections import namedtuple
from typing import Sequence
from github.GithubException import RateLimitExceededException, GithubException
from requests.exceptions import ConnectionError
from pilz_github_ci_runner.pull_request_validator import PullRequestValidator
from pilz_github_ci_runner.hardware_tester import HardwareTester
from pilz_github_ci_runner.user_interface import ask_user_for_pr_to_check


class PRCheckExecutor(object):
    """ This class handles the github conntection.
        It also fetches and tests valid pullrequests.
    """
    def __init__(self, token, repo_name: str, allowed_users: Sequence[str], tester: HardwareTester, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__token = token
        self.__repo_name = repo_name
        self.__allowed_users = allowed_users
        self.__hardware_tester = tester
        self.__create_repo_handler()

    def __create_repo_handler(self):
        gh = github.Github(self.__token)
        self.__test_bot_account = gh.get_user().login
        self.__repo = gh.get_repo(self.__repo_name)

    def check_and_execute_loop(self, loop_time):
        while True:
            start = time.time()
            self.test_prs(manually=False)
            end = time.time()
            remain = int(loop_time) - (end - start)
            if remain > 0:
                time.sleep(remain)

    def test_prs(self, manually=True):
        try:
            testable_prs = self._get_testable_pull_requests()
            if manually:
                self.__hardware_tester.check_prs(ask_user_for_pr_to_check(testable_prs))
            else:
                for p in testable_prs:
                    if p.head_is_untested:
                        self.__hardware_tester.check_pr(p)
        except RateLimitExceededException:
            print("Reached a rate limit on Github please try again later.")
        except GithubException:
            print("An unspecified Exception from Github had occured.")
        except ConnectionError:
            print("Remote client disconnected unexpectedly. Please retry again later.")
            self.__create_repo_handler()


    def _get_testable_pull_requests(self):
        testable_pull_requests = []
        print(f"{'>'*50}\nSearching for PRs to test.\n" % ())
        for pr in self.__repo.get_pulls():
            pr.__class__ = PullRequestValidator
            pr.validate(self.__allowed_users, self.__test_bot_account)
            print(pr.status_report(long=True))
            if pr.is_valid():
                testable_pull_requests.append(pr)
        print("<"*50)
        return testable_pull_requests
