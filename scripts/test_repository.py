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
        [--dry-run]
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
    --dry-run                    Don't comment on the github pull requests. For testing purposes.
"""


from pilz_github_ci_runner import *
from pilz_github_ci_runner.print_redirector import PrintRedirector

import os
import sys
import time
import shlex
import docopt
import contextlib

from pathlib import Path
from github.GithubException import UnknownObjectException

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


DESCRIPTION = """
    To enable Testing in a PullRequest(PR) add '- [ ] Perform hardware tests' to your PR description.

    Only internal PRs will be tested by default.
    To allow testing on PRs from forks, a User in the ALLOWED_USERS list has to accept the head commit of this PR.
    To allow the head commit write a comment with: 'Allow hw-tests up to commit [sha]'
        [sha] has to equal the full sha of the last commit in this PR.

    For further Information see https://github.com/PilzDE/pilz_testutils/pilz_github_ci_runner.

"""


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
    print(DESCRIPTION)

    if arguments.get('set-token'):
        exit(1) if set_token() else exit(0)

    token = get_token(no_keyring=arguments.get('--no-keyring'))

    allowed_users = shlex.split(arguments.get("ALLOWED_USERS"))

    log_dir = os.path.expanduser(arguments.get("--log"))
    tester = HardwareTester(ci_args=parse_ci_args(arguments.get("CI_ARGS")),
                            token=token,
                            log_dir=log_dir,
                            setup_cmd=arguments.get("--setup-cmd"),
                            cleanup_cmd=arguments.get("--cleanup-cmd"),
                            dry_run=arguments.get("--dry-run"))

    try:
        check_executor = PRCheckExecutor(
            token, arguments.get("REPO"), allowed_users, tester)
    except UnknownObjectException:
        print("Repository not found! Please check the spelling of the REPO argument")
        exit(1)

    loop_time = arguments.get("--loop-time", None)

    with contextlib.suppress(KeyboardInterrupt):
        with PrintRedirector(Path(log_dir) / Path("stdout.log")):
            if not loop_time:
                check_executor.test_prs()
            else:
                check_executor.check_and_execute_loop(loop_time)
