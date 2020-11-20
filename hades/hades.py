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
import yaml

import istarmap

def main():
    with open ('python.yaml', 'r') as file:
        config = yaml.safe_load(file)

    hades = Hades(config)
    hades.run_plagiarism_check()

class Hades():
    __file_paths: List[str] = []
    __strings: List[str] = []
    __junk_function0 = None
    __junk_function1 = lambda c: c.isspace()
    __ratios: List[tuple] = []

    def __init__(self, config):
        self.file_extensions = config['file_extensions']

        self.dir_name = config['dir_name']
        self.number_of_top_results = config['number_of_top_results']
        self.reports_dir = config['reports_dir']
        self.number_of_processes = config['number_of_processes']

        self.best_matches = []

        self.__get_list_of_files()
        self.__file_paths_to_strings()

    def __get_list_of_files(self):
        """Get the list of all files in directory tree at given path"""
        self.__file_paths = []
        for (dirpath, _, filenames) in os.walk(self.dir_name):
            self.__file_paths += [os.path.join(dirpath, file)
                                for file in filenames if self.__file_satisfies_conditions(file)]

    def __file_satisfies_conditions(self, file_name):
        for file_extension in self.file_extensions:
            if file_name.endswith(file_extension):
                return True
        return False

    def __file_paths_to_strings(self):
        """Reads the files indicates by file_paths into a list of strings"""
        self.__strings = []
        for file_path in self.__file_paths:
            with open(file_path, 'r') as file:
                self.__strings.append(file.read().replace('\n', ''))

    def run_plagiarism_check(self):
        """
        Runs an actual plagiarism check, from file comparison, sorting
        the results to producing output
        """
        self.__compare_combinations()
        self.__sort_results()
        self.__print_summary()
        self.__generate_reports()

    def __compare_combinations(self):
        """
        Compare all pair-wise combinations of strings, in parallel,
        and create a list of tuples (ratio, file_path0, file_path1).
        """
        number_of_combinations = math.comb(len(self.__strings), 2)
        print('Comparing', len(self.__strings), 'files in',
              number_of_combinations, 'combinations using',
              self.number_of_processes, 'processes...', flush=True)

        # Create a list of tuples (ratio, file_path0, file_path1)
        # Uses a workaround to use tqdm with starmap
        # Source: https://stackoverflow.com/questions/57354700/starmap-combined-with-tqdm
        with Pool(processes=self.number_of_processes) as pool:
            iterable = itertools.combinations(range(len(self.__strings)), 2)
            for result in tqdm.tqdm(pool.istarmap(self.sequence_matcher_wrapper, iterable),
                                    total=number_of_combinations):
                self.__ratios.append(result)

        # For when not using tqdm to indicate progress
        # self.ratios = pool.starmap(sequence_matcher_wrapper,
        #                       itertools.combinations(range(len(STRINGS)), 2))

    def sequence_matcher_wrapper(self, idx0, idx1):
        """
        A wrapper for the SequenceMatcher from difflib.
        This makes it work with multiprocessing.
        """
        ratio = SequenceMatcher(self.__junk_function0,
                                self.__strings[idx0], self.__strings[idx1]).ratio()
        return ratio, self.__file_paths[idx0], self.__file_paths[idx1]

    def __sort_results(self):
        """Sorts the results and puts the best matches in best_matches"""
        print('Sorting ratios...', end='', flush=True)
        self.__ratios.sort(reverse=True)
        self.best_matches = self.__ratios[0:self.number_of_top_results]
        print(' Done')

    def __print_summary(self):
        """Prints summary of the results to the terminal"""
        print('Showing the ' + str(self.number_of_top_results) + ' best matches:')
        pretty_printer = pprint.PrettyPrinter(width=200)
        pretty_printer.pprint(self.best_matches)

    def __generate_reports(self):
        """
        Creates a `reports' directory and create a report (.txt) for the
        closest matches. Each reports contains the ratio, two file paths,
        and the contents of the files
        """
        print('Generating reports...', end='', flush=True)
        separator = '\n' + '-' * 80 + '\n'
        pathlib.Path(self.reports_dir).mkdir(parents=True, exist_ok=True)
        for idx, (ratio, file_path0, file_path1) in enumerate(self.best_matches):
            with open(self.reports_dir + '/' + str(idx) + '.txt', 'w') as file:
                file.write('Match ratio: ' + str(ratio) + '\n')
                file.write('File 0: ' + file_path0 + '\n')
                file.write('File 1: ' + file_path1 + '\n')
                file.write(separator)
                with open(file_path0, 'r') as file0:
                    file.write(file0.read())
                file.write(separator)
                with open(file_path1, 'r') as file1:
                    file.write(file1.read())
        print(' Reports written to ' + self.reports_dir + '/')

if __name__ == '__main__':
    main()
