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

import re
GITHUB_OUTPUT_CAP = 262144


def collapse_sections(output: str) -> str:
    """ Add github collapse sections for the ci output """
    output = _clean_from_unknown_characters(output)
    output = _collapse_ci_main_sections(output)
    output = _colorize_results(output)
    output = _add_codeblocks_for_test_output(output)
    output = _crop_output_to_comment_max_length(output)
    return f"<details>\n<summary>Output</summary>\n\n{output}\n</details>"


def _clean_from_unknown_characters(output: str) -> str:
    output = re.sub(r'\[\d*(m|K)', "", output)
    output = re.sub(r'', "\n   ", output)
    return re.sub(r'', "", output)


def _collapse_ci_main_sections(output: str) -> str:
    output = re.sub(r'>{62}', "<details><summary>", output)
    output = re.sub(r'<{62}', "</details>\n", output)
    return _add_collapse_title_ends(output)


def _add_collapse_title_ends(output: str) -> str:
    lines = output.splitlines(keepends=True)
    for i, l in enumerate(lines):
        if "<summary>" in l:
            lines[i+1] += "</summary>\n\n"
    return "".join(lines)


def _colorize_results(output: str) -> str:
    lines = output.splitlines(keepends=True)
    for i, l in enumerate(lines):
        if "returned with code '" in l:
            lines[i] = "```diff\n%s%s\n```\n" % (
                "+" if "code '0'" in l else "-", l)
        if "Summary: " in l and "package finished" not in l:
            lines[i] = "```diff\n%s%s\n```\n" % (
                "+" if "0 errors" in l and "0 failures" in l else "-", l)
    return "".join(lines)


def _add_codeblocks_for_test_output(output: str) -> str:
    return re.sub(r'\n---', "\n\n```\n\n", output)


def _crop_output_to_comment_max_length(output: str) -> str:
    REMOVED_MSG = "\nREMOVED SOME LINES FROM OUTPUT TO COMPLY TO COMMENT MAX LENGTH!"
    deleted = False
    while len(output) > GITHUB_OUTPUT_CAP - len(REMOVED_MSG):
        deleted = True
        output, number_ob_subs = re.subn(
            r'(?<=<\/summary>)(((?!<\/details>).)*\n)+', "...", output, count=1)
        if number_ob_subs == 0:
            return("Could not comply to comment max length by erasing section content for some reason."
                   "\nPlease check the CI log for further information.")
    return output + REMOVED_MSG if deleted else output
