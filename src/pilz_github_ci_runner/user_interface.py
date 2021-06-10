import contextlib
from typing import Sequence


def ask_user_for_pr_to_check(testable_prs: Sequence) -> Sequence:
    print("="*30)
    if len(testable_prs) > 0:
        _print_prs_that_are_ready_for_testing(testable_prs)
    else:
        print("No Pullrequests ready to test.")
        print("="*30)
        return []
    return _let_the_user_select_prs(testable_prs)


def _print_prs_that_are_ready_for_testing(testable_prs):
    print("Pull Requests ready for Testing:")
    for n, tp in enumerate(testable_prs):
        print("  %s) #%s - %s" % (n, tp.number, tp.title))


def _let_the_user_select_prs(testable_prs):
    print("\nPlease select tests to execute (comma separated, with 'ID' or '#NR'): ")
    prs_to_check = _get_selected_prs(input().split(","), testable_prs)
    print("Will test PRs: %s" % prs_to_check)
    return prs_to_check


def _get_selected_prs(selection, testable_prs):
    prs_to_check = []
    for p in selection:
        with contextlib.suppress((IndexError, ValueError)):
            if p.startswith("#"):
                for tp in testable_prs:
                    if tp.number == int(p[1:]):
                        prs_to_check.append(tp)
                        break
            else:
                prs_to_check.append(testable_prs[int(p)])
    return prs_to_check
