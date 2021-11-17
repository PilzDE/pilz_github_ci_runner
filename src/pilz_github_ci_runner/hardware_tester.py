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

from typing import Sequence
from tempfile import TemporaryDirectory
from pathlib import Path
from github.PullRequest import PullRequest
from .print_redirector import PrintRedirector
from .output_format import collapse_sections
import os
import time
import subprocess
import yaml


class HardwareTester(object):
    """ This Class fetches the sources, runs the industrial ci and reports back the result to the PullRequest.
    """

    def __init__(self, token: str, log_dir: str, ci_args: {}, setup_cmd: str, cleanup_cmd: str, dry_run: bool, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token = token
        self._log_dir = log_dir
        self._env = _gather_ci_environment_variables(ci_args)
        self._setup_cmd = setup_cmd
        self._cleanup_cmd = cleanup_cmd
        self._dry_run = dry_run

    def check_prs(self, prs_to_check: Sequence[PullRequest]):
        """ Runs the CI for several PullRequest objects """
        for pr in prs_to_check:
            self.check_pr(pr)

    def check_pr(self, pr: PullRequest):
        """ Fetches a PullRequest and runs the industrial CI for it. """
        repo = pr.base.repo
        print(f"Starting test of PR #{pr.number}")
        if not self._dry_run:
            pr.create_issue_comment(f"Starting a test for {pr.head.sha}")
        if self._setup_cmd:
            _run_command(self._setup_cmd)
        with PrintRedirector(Path(self._log_dir) / Path(self._get_log_file_name(pr))):
            with TemporaryDirectory() as t:
                _run_command(
                    f"git clone https://{self._token}@github.com/{repo.full_name}.git", cwd=t)
                repo_dir = os.path.join(t, repo.name)
                _run_command(
                    "git config advice.detachedHead false", cwd=repo_dir)
                _run_command(
                    f"git fetch origin pull/{pr.number}/merge", cwd=repo_dir)
                _run_command(
                    "git checkout FETCH_HEAD", cwd=repo_dir)
                _extend_env_from_config_file(repo_dir, self._env)
                result = run_tests(
                    repo_dir, self._env)

        result_msg = "SUCCESSFULL" if not result["return_code"] else "WITH %s FAILURES" % result["return_code"]
        end_text = f"Finished test of {pr.head.sha}: {result_msg}"
        print(end_text)

        co = collapse_sections(result["output"])
        if not self._dry_run:
            pr.create_issue_comment(f"{end_text}\n{co}")
        if self._cleanup_cmd:
            _run_command(self._cleanup_cmd)

    def _get_log_file_name(self, pr: PullRequest) -> str:
        head_commit = list(pr.get_commits())[-1].sha
        t = time.strftime("(%Y%b%d_%H:%M:%S)", time.localtime())
        return f"{head_commit}_{t}.log"


def _gather_ci_environment_variables(ci_args: {}) -> {}:
    relevant_env = os.environ.copy()
    relevant_env.update(ci_args)
    return relevant_env


def _run_command(command: str, **kwargs):
    print(f"\n{'>'*50}\nExecuting: {command}\n")
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, shell=True, **kwargs)
    full_output = ""
    while True:
        output = process.stdout.readline().decode()
        if output == '' and process.poll() is not None:
            break
        if output:
            full_output += output
            print(output.strip())

    return_code = process.poll()
    print("<"*50)
    return {"return_code": return_code, "output": full_output}


def _extend_env_from_config_file(repo_dir, env: {}):
    config_file = repo_dir + "/.pilz_github_ci_runner.yml"
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
            env['ROS_DISTRO'] = config['ROS_DISTRO']  # Only ROS_DISTRO allowed
    except:
        # Ignore if no file is given. Default given at start of runner will be used. Needed for backward compatibility.
        pass


def run_tests(dir, env: {}):
    """ Runs the industrial CI on a ros package directory.
        Needs ROS and industrial CI sourced.

        :param dir: Path to the ros package to test
    """
    command = 'rosrun industrial_ci run_ci'
    print('Running {}'.format(command))
    return _run_command(command, env=env, cwd=os.path.expanduser(dir))
