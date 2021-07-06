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

from tempfile import TemporaryDirectory
from pathlib import Path
from .print_redirector import PrintRedirector
import os
import time
import subprocess


KEYS = ["ROS_DISTRO", "ROS_REPO", "DOCKER_RUN_OPTS", "APT_PROXY", "CMAKE_ARGS",
        "ROS_MASTER_URI", "ROS_PYTHON_VERSION", "ROS_PACKAGE_PATH", "ROS_ROOT",
        "ROS_VERSION", "ROS_ETC_DIR", "PYTHONPATH", "ROSLISP_PACKAGE_DIRECTORIES",
        "PATH"]


class HardwareTester(object):
    def __init__(self, token, log_dir, ci_args, setup_cmd, cleanup_cmd, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._token = token
        self._log_dir = log_dir
        self._env = gather_ci_environment_variables(ci_args)
        print("CI Environment:", self._env)
        self._setup_cmd = setup_cmd
        self._cleanup_cmd = cleanup_cmd

    def check_prs(self, prs_to_check):
        for pr in prs_to_check:
            self.check_pr(pr)

    def _get_log_file_name(self, pr) -> str:
        return "%s_%s.log" % (list(pr.get_commits())[-1].sha,
                              time.strftime("(%Y%b%d_%H:%M:%S)", time.localtime()))

    def check_pr(self, pr):
        repo = pr.base.repo
        print("Starting test of PR #%s" % pr.number)
        pr.create_issue_comment("Starting a test for %s" % pr.head.sha)
        if self._setup_cmd:
            run_command(self._setup_cmd)
        with PrintRedirector(Path(self._log_dir) / Path(self._get_log_file_name(pr))):
            with TemporaryDirectory() as t:
                run_command(
                    "git clone https://%s@github.com/%s.git" % (self._token, repo.full_name), cwd=t)
                repo_dir = os.path.join(t, repo.name)
                run_command(
                    "git config advice.detachedHead false", cwd=repo_dir)
                run_command(
                    "git fetch origin pull/%s/merge" % pr.number, cwd=repo_dir)
                run_command(
                    "git checkout FETCH_HEAD", cwd=repo_dir)
                result = run_tests(
                    repo_dir, self._env)

        end_text = "Finished test of %s: %s" % (
            pr.head.sha, "SUCCESSFULL" if not result["return_code"] else "WITH %s FAILURES" % result["return_code"])
        print(end_text)

        pr.create_issue_comment(
            "%s\n<details>\n<summary>Output</summary>\n\n```\n%s\n```" % (end_text, result["output"]))
        if self._cleanup_cmd:
            run_command(self._cleanup_cmd)


def gather_ci_environment_variables(ci_args):
    # relevant_env = _read_selected_variables_from_os_envirement(KEYS)
    relevant_env = os.environ.copy()
    relevant_env.update(ci_args)
    return relevant_env


def _read_selected_variables_from_os_envirement(selected_keys) -> dict:
    return {k: os.environ.get(k) for k in selected_keys if k in os.environ}


def run_command(command, **kwargs):
    print("\n%s\nExecuting: %s\n" % (">"*50, command))
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


def run_tests(dir, env):
    print(env)
    # Needs sources ROS and path to industrial_ci
    command = 'rosrun industrial_ci run_ci'
    print('Running {}'.format(command))
    return run_command(command, env=env, cwd=os.path.expanduser(dir))
