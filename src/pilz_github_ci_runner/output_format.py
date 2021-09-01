def clean_from_unknown_characters(output: str):
    new_output = ""
    deleteMode = False
    for char in output:
        if char == "":
            deleteMode = True
        if not deleteMode:
            if char == "":
                new_output += "\n   "
            elif char == "":
                new_output += ""
            else:
                new_output += char
        if deleteMode and char == "m" or char == "K":
            deleteMode = False
    return new_output


def collapse_sections(output):
    collapsed_outout = ""
    in_title = False
    for line in output.split("\n"):
        if ">" * 60 in line:
            collapsed_outout += "<details><summary>"
            in_title = True
        elif "<" * 60 in line:
            collapsed_outout += "\n\n</details>\n\n"
        else:
            if line.startswith("---"):
                line = line.replace("---", "\n\n```\n\n")
            collapsed_outout += line
            if in_title:
                collapsed_outout += "</summary>\n\n"
                in_title = False
            else:
                collapsed_outout += "\n"
    return collapsed_outout.rstrip()
