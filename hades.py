"""
Hades, a plagiarism checker.
"""
from difflib import SequenceMatcher
from multiprocessing import Pool
from typing import List

import itertools
import math
import os
import pathlib
import pprint
import tqdm

import istarmap

FILE_PATHS: List[str] = []
STRINGS: List[str] = []
JUNK_FUNCTION0 = None
JUNK_FUNCTION1 = lambda c: c.isspace()

def main():
    dir_name = './'
    number_of_top_results = 20
    reports_dir = 'reports'
    number_of_processes = 2

    run_plagiarism_check(dir_name, number_of_top_results, reports_dir, number_of_processes)


def sequence_matcher_wrapper(idx0, idx1):
    """
    A wrapper for the SequenceMatcher from difflib.
    This makes it work with multiprocessing.
    """
    ratio = SequenceMatcher(JUNK_FUNCTION0, STRINGS[idx0], STRINGS[idx1]).ratio()
    return ratio, FILE_PATHS[idx0], FILE_PATHS[idx1]


def run_plagiarism_check(dir_name, number_of_top_results, reports_dir, number_of_processes):
    """
    Performs the actual plagiarism checking
    and outputs the results to stdout and files
    """
    global FILE_PATHS
    global STRINGS
    FILE_PATHS = get_list_of_files(dir_name)
    STRINGS = file_paths_to_strings(FILE_PATHS)

    number_of_combinations = math.comb(len(STRINGS), 2)
    print('Comparing', len(STRINGS), 'files in',
          number_of_combinations, 'combinations using',
          number_of_processes, 'processes...', flush=True)

    # Create a list of tuples (ratio, file_path0, file_path1)
    # Uses a workaround to use tqdm with starmap
    # Source: https://stackoverflow.com/questions/57354700/starmap-combined-with-tqdm
    ratios = []
    with Pool(processes=number_of_processes) as pool:
        iterable = itertools.combinations(range(len(STRINGS)), 2)
        for result in tqdm.tqdm(pool.istarmap(sequence_matcher_wrapper, iterable),
                                total=number_of_combinations):
            ratios.append(result)

    # For when not using tqdm to indicate progress
    # ratios = pool.starmap(sequence_matcher_wrapper,
    #                       itertools.combinations(range(len(STRINGS)), 2))

    # Sort to find the files which are most similar
    print('Sorting ratios...', end='', flush=True)
    ratios.sort(reverse=True)
    best_matches = ratios[0:number_of_top_results]
    print(' Done')

    print('Showing the ' + str(number_of_top_results) + ' best matches:')
    pretty_printer = pprint.PrettyPrinter(width=200)
    pretty_printer.pprint(best_matches)

    # Generate reports
    print('Generating reports...', end='', flush=True)
    separator = '\n' + '-' * 80 + '\n'
    pathlib.Path(reports_dir).mkdir(parents=True, exist_ok=True)
    for idx, (ratio, file_path0, file_path1) in enumerate(best_matches):
        with open(reports_dir + '/' + str(idx) + '.txt', 'w') as file:
            file.write('Match ratio: ' + str(ratio) + '\n')
            file.write('File 0: ' + file_path0 + '\n')
            file.write('File 1: ' + file_path1 + '\n')
            file.write(separator)
            with open(file_path0, 'r') as file0:
                file.write(file0.read())
            file.write(separator)
            with open(file_path1, 'r') as file1:
                file.write(file1.read())
    print(' Reports written to ' + reports_dir + '/')


def get_list_of_files(dir_name):
    """Get the list of all files in directory tree at given path"""
    file_paths = []
    for (dirpath, _, filenames) in os.walk(dir_name):
        file_paths += [os.path.join(dirpath, file) for file in filenames if file.endswith('.py')]
    return file_paths


def file_paths_to_strings(file_paths):
    """Reads the files indicates by file_paths into a list of strings"""
    strings = []
    for file_path in file_paths:
        with open(file_path, 'r') as file:
            strings.append(file.read().replace('\n', ''))
    return strings


if __name__ == '__main__':
    main()
