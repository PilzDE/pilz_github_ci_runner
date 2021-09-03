import re
GITHUB_OUTPUT_CAP = 262144


def collapse_sections(output):
    output = clean_from_unknown_characters(output)
    output = create_sections(output)
    output = create_code_blocks(output)
    output = crop_output_to_max_length(output)
    return "<details>\n<summary>Output</summary>\n\n%s\n</details>" % output


def clean_from_unknown_characters(output: str):
    output = re.sub(r'\[\d*(m|K)', "", output)
    output = re.sub(r'', "\n   ", output)
    return re.sub(r'', "", output)


def create_sections(output):
    output = re.sub(r'>{62}', "<details><summary>", output)
    output = re.sub(r'<{62}', "</details>\n", output)
    return create_summary_end_and_colorize_result(output)


def create_summary_end_and_colorize_result(output):
    lines = output.splitlines(keepends=True)
    for i, l in enumerate(lines):
        if "<summary>" in l:
            lines[i+1] += "</summary>\n\n"
        if "returned with code '" in l:
            lines[i] = "```diff\n%s%s\n```\n" % (
                "+" if "code '0'" in l else "-", l)
    return "".join(lines)


def create_code_blocks(output):
    return re.sub(r'\n---', "\n\n```\n\n", output)


def crop_output_to_max_length(output):
    REMOVED_MSG = "\nREMOVED SOME LINES FROM OUTPUT TO COMPLY TO COMMENT MAX LENGTH!"
    deleted = False
    while len(output) > GITHUB_OUTPUT_CAP - len(REMOVED_MSG):
        deleted = True
        output, number_ob_subs = re.subn(
            r'(?<=<\/summary>)(((?!<\/details>).)*\n)+', "...", output, count=1)
        if number_ob_subs == 0:
            return("Could not comply to comment max lenth by erasing section connent for some reason."
                   "\nPlease check the CI log for further information.")
    return output + REMOVED_MSG if deleted else output
