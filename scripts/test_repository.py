#! /usr/bin/env python

"""Automated Hardware Testing

Usage:
    pilz_github_ci_runner.py REPO ALLOWED_USERS ...
        [--log=LOG_DIR]
        [--docker_opts=DOCKER_OPTS]
        [--apt_proxy=APT_PROXY]
        [--cmake_args=CMAKE_ARGS]
        [--setup_cmd=SETUP_CMD]
        [--cleanup_cmd=SETUP_CMD]
        [--loop_time=MIN_TIME_IN_SEC]
    pilz_github_ci_runner.py set-token

   e.g. pilz_github_ci_runner.py max/awesome_repo max theOtherOne AwesomeGuy

Options:
    -h --help                    Show this
    --log=LOG_DIR                Test log directory [default: ~/.ros/hardware_tests/]
    --docker_opts=DOCKER_OPTS    Options that will be passed to the industrial ci
    --cmake_args=CMAKE_ARGS      Arguments that will be passed to the cmake run
    --apt_proxy=APT_PROXY
    --setup_cmd=SETUP_CMD        Command to run before starting industrial_ci e.g. for starting hardware
    --cleanup_cmd=CLEANUP_CMD    Command to run after industrial_ci has finished e.g. for stopping hardware
    --loop_time=MIN_TIME_IN_SEC  If set automatically searches valid pull requests and executes the tests continuosly.
                                 The argument provided is the minimum repeat time of the loop in seconds.
"""


from pilz_github_ci_runner import get_testable_pull_requests, ask_user_for_pr_to_check, HardwareTester
from pilz_github_ci_runner.print_redirector import PrintRedirector

import os
import sys
import time
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
        tester.check_prs(get_testable_pull_requests(
            repo, allowed_users, test_bot_account))
        end = time.time()
        remain = int(loop_time) - (end - start)
        if remain > 0:
            time.sleep(remain)


if __name__ == "__main__":
    arguments = docopt.docopt(__doc__)
    print(arguments, "\n")

    if arguments.get('set-token'):
        if set_token():
            exit(1)
        else:
            exit(0)

    token = get_token()
    try:
        gh = github.Github(token)
        test_bot_account = gh.get_user().login
        repo = gh.get_repo(arguments.get("REPO"))
    except UnknownObjectException:
        print("Repository not found! Please check the spelling of the REPO argument")
        exit(1)
    log_dir = os.path.expanduser(arguments.get("--log"))
    docker_opts = arguments.get("--docker_opts")
    cmake_args = arguments.get("--cmake_args")
    allowed_users = arguments.get("ALLOWED_USERS")
    apt_proxy = arguments.get("--apt_proxy")
    setup_cmd = arguments.get("--setup_cmd")
    cleanup_cmd = arguments.get("--cleanup_cmd")
    loop_time = arguments.get("--loop_time", None)

    tester = HardwareTester(docker_opts=docker_opts,
                            cmake_args=cmake_args,
                            token=token,
                            apt_proxy=apt_proxy,
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
