#! /usr/bin/env python

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

"""Automated Hardware Testing

Usage:
    pilz_github_ci_runner.py REPO ALLOWED_USERS [CI_ARGS ...]
        [--log=LOG_DIR]
        [--setup-cmd=SETUP_CMD]
        [--cleanup-cmd=SETUP_CMD]
        [--loop-time=MIN_TIME_IN_SEC]
        [--no-keyring]
    pilz_github_ci_runner.py set-token

   Arguments for the CI can either be set as environment variables or passed as arguments.
   e.g. APT_PROXY=192.168.0.1 pilz_github_ci_runner.py "max/awesome_repo max theOtherOne AwesomeGuy"
   or   pilz_github_ci_runner.py max/awesome_repo "max theOtherOne" APT_PROXY=192.168.0.1 ROS_DISTRO=noetic

Options:
    -h --help                    Show this
    --log=LOG_DIR                Test log directory [default: ~/.ros/hardware_tests/]
    --setup-cmd=SETUP_CMD        Command to run before starting industrial_ci e.g. for starting hardware
    --cleanup-cmd=CLEANUP_CMD    Command to run after industrial_ci has finished e.g. for stopping hardware
    --loop-time=MIN_TIME_IN_SEC  If set automatically searches valid pull requests and executes the tests continuosly.
                                 The argument provided is the minimum repeat time of the loop in seconds.
    --no-keyring                 Will ask for the token directly, instead of using the keyring.
"""


from pilz_github_ci_runner import get_testable_pull_requests, ask_user_for_pr_to_check, HardwareTester
from pilz_github_ci_runner.print_redirector import PrintRedirector

import os
import sys
import time
import shlex
import docopt
import github
import contextlib
import keyring

from pathlib import Path
from getpass import getpass
from github.GithubException import RateLimitExceededException, UnknownObjectException

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


def set_token():
    token = None
    while not token:
        print(
            "Please provide a GitHub personal access token with 'public_repo' permission.")
        new_token = getpass(prompt='personal access token:')
        keyring.set_password(
            'system', 'github-hardware-tester-token', new_token)
        token = keyring.get_password('system', 'github-hardware-tester-token')
        if not token:
            print("There was an issue storing the token in the keyring!")
    return token


def get_token():
    keyring.set_keyring(
        keyring.backends.SecretService.Keyring())  # For Ubuntu 20
    token = keyring.get_password('system', 'github-hardware-tester-token')
    if not token:
        token = set_token()
    return token


def check_and_execute_loop(loop_time):
    while True:
        start = time.time()
        for p in get_testable_pull_requests(repo, allowed_users, test_bot_account):
            if p.head_is_untested:
                tester.check_pr(p)
        end = time.time()
        remain = int(loop_time) - (end - start)
        if remain > 0:
            time.sleep(remain)


def parse_ci_args(cias):
    ci_env = {}
    for a in cias:
        with contextlib.suppress(ValueError):
            key, value = a.split("=", maxsplit=1)
            ci_env[key] = value
    return ci_env


if __name__ == "__main__":
    arguments = docopt.docopt(__doc__)
    print(arguments, "\n")

    if arguments.get('set-token'):
        if set_token():
            exit(1)
        else:
            exit(0)

    if arguments.get('--no-keyring'):
        token = getpass(prompt='personal access token:')
    else:
        token = get_token()

    try:
        gh = github.Github(token)
        test_bot_account = gh.get_user().login
        repo = gh.get_repo(arguments.get("REPO"))
    except UnknownObjectException:
        print("Repository not found! Please check the spelling of the REPO argument")
        exit(1)

    allowed_users = shlex.split(arguments.get("ALLOWED_USERS"))
    log_dir = os.path.expanduser(arguments.get("--log"))
    loop_time = arguments.get("--loop-time", None)
    setup_cmd = arguments.get("--setup-cmd")
    cleanup_cmd = arguments.get("--cleanup-cmd")

    ci_args = parse_ci_args(arguments.get("CI_ARGS"))

    tester = HardwareTester(ci_args=ci_args,
                            token=token,
                            log_dir=log_dir,
                            setup_cmd=setup_cmd,
                            cleanup_cmd=cleanup_cmd)

    desciption = """
    To enable Testing in a PullRequest(PR) add '- [ ] Perform hardware tests' to your PR description.

    Only internal PRs will be tested by default.
    To allow testing on PRs from forks, a User in the ALLOWED_USERS list has to accept the head commit of this PR.
    To allow the head commit write a comment with: 'Allow hw-tests up to commit [sha]'
        [sha] has to equal the full sha of the last commit in this PR.

    For further Information see https://github.com/PilzDE/pilz_testutils/pilz_github_ci_runner.

    """
    print(desciption)

    with contextlib.suppress(KeyboardInterrupt):
        try:
            with PrintRedirector(Path(log_dir) / Path("stdout.log")):
                if not loop_time:
                    tester.check_prs(ask_user_for_pr_to_check(
                        get_testable_pull_requests(repo, allowed_users, test_bot_account)))
                else:
                    check_and_execute_loop(loop_time)
        except RateLimitExceededException:
            print("Reached a rate limit on Github please try again later.")
