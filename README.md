# Github Hardware Tests
This package provides a python script periodically for periodically checking a github repo and running tests for PullRequests using [industrial_ci](https://github.com/ros-industrial/industrial_ci).

To avoid running arbitrary PRs on the machine only PullRequests containing the string "- [ ] Perform hardware tests" and with commits from allowed users are checked. The start and finish of the test are reported with a comment on the issue.

## Prequisites
In order to run the script you need:
- Docker installed on the machine
- A personal token with "public_repo" scope
- `industrial_ci` installed locally and sourced (see instructions [here](https://github.com/ros-industrial/industrial_ci/blob/master/doc/index.rst#simplest-way-to-run-locally))
## Usage
For example the tests running on https://github.com/PilzDE/psen_scan_v2 use:
```
rosrun pilz_github_ci_runner test_repository.py "PilzDE/psen_scan_v2" \
"rfeistenauer agutenkunst" \
--setup_cmd="usbrelay 1_1=0; sleep 2; usbrelay 1_1=1" --cleanup_cmd="usbrelay 1_1=0" \
--cmake-args="DENABLE_HARDWARE_TESTING=ON"
APT_PROXY=http://172.20.20.104:3142 \
DOCKER_RUN_OPTS="-v /usr/local/share/ca-certificates:/usr/local/share/ca-certificates:ro --env HOST_IP=192.168.0.122 --env SENSOR_IP=192.168.0.100" \
```
For continuous running add a `--loop_time=<seconds_for_refresh>`

## Security considerations
The tests are only run if the pull request

- is created from allowed users and originate from a branch within the same repo.
- and contain the string "- [ ] Perform hardware tests" in the description.

or

- originates from a fork by an arbitrary (including allowed) user
- and have an issue comment "Allow hw-tests up to commit [sha]" from an allowed user. Where [sha] is the latests commit on the *head*-branch to be merged into the *base*.
- and contain the string "- [ ] Perform hardware tests" in the description.

Note:
- Even pull requests from forks of allowed users are not permitted per default since the write rights could be extended in the fork.

## Background
This package originates from the desire the to have test running with actual hardware that are triggered by Github PullRequests. While Github offers so called "[Self-hosted runners](https://docs.github.com/en/actions/hosting-your-own-runners)" these are critical when working with public repos (see [here](https://docs.github.com/en/actions/hosting-your-own-runners/about-self-hosted-runners#self-hosted-runner-security-with-public-repositories), [here](https://github.community/t/self-hosted-runner-security-with-public-repositories/17860/11) and [here](https://github.com/actions/runner/issues/494)). Until a better solution is available we stick with this approach ensuring some security by allowing only code from or approved by dedicated users to be run the local machine in order to mitigate some of the security concerns.
