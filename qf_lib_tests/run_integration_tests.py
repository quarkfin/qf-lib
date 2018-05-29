import os
import sys

from os.path import dirname, join

from qf_lib.get_sources_root import get_src_root

sys.path[0] = os.getcwd()  # dirty hack to make python interpreter know where to look for the modules to import


def main():
    from qf_lib_tests.helpers.run_tests_from_directory import run_tests_and_print_results
    tests_directory = join(dirname(__file__), "integration_tests")
    was_successful = run_tests_and_print_results(tests_directory, top_level_dir=get_src_root())
    sys.exit(not was_successful)


if __name__ == '__main__':
    main()
