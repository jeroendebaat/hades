from difflib import SequenceMatcher
from multiprocessing import Pool, TimeoutError
from typing import List
import math
import itertools
import os
import pathlib
import pprint

filePaths: List[str] = []
strings: List[str] = []
junkFunction0 = None
junkFunction1 = lambda c: c.isspace()

def main():
    DIRNAME = './';
    NUMBER_OF_TOP_RESULTS = 20
    REPORTS_DIR = 'reports'

    runPlagiarismCheck(DIRNAME, NUMBER_OF_TOP_RESULTS, REPORTS_DIR)

def sequenceMatcherWrapper(idx0, idx1):
    ratio = SequenceMatcher(junkFunction0, strings[idx0], strings[idx1]).ratio()
    return ratio, filePaths[idx0], filePaths[idx1]

def runPlagiarismCheck(dirName, numberOfTopResults, reportsDir):
    global filePaths
    global strings
    filePaths = getListOfFiles(dirName)
    strings = filePathsToStrings(filePaths)

    print("Comparing", len(strings), "files in",
          math.comb(len(strings), 2), "combinations...", end='', flush=True)

    # Create a list of tuples (ratio, filePath0, filePath1)
    with Pool(processes=2) as pool:
        ratios = pool.starmap(sequenceMatcherWrapper,
                              itertools.combinations(range(len(strings)), 2))
    print(' Done')

    # Sort to find the files which are most similar
    print('Sorting ratios...', end='', flush=True)
    ratios.sort(reverse=True)
    bestMatches = ratios[0:numberOfTopResults]
    print(' Done')

    print('Showing the ' + str(numberOfTopResults) + ' best matches:')
    pp = pprint.PrettyPrinter(width=200)
    pp.pprint(bestMatches)

    # Generate reports
    print('Generating reports...', end='', flush=True)
    separator = '\n' + '-' * 80 + '\n'
    pathlib.Path(reportsDir).mkdir(parents=True, exist_ok=True)
    for idx, (ratio, filePath0, filePath1) in enumerate(bestMatches):
        with open(reportsDir + '/' + str(idx) + '.txt', 'w') as file:
            file.write('Match ratio: ' + str(ratio) + '\n')
            file.write('File 0: ' + filePath0 + '\n')
            file.write('File 1: ' + filePath1 + '\n')
            file.write(separator)
            with open(filePath0, 'r') as file0:
                file.write(file0.read())
            file.write(separator)
            with open(filePath1, 'r') as file1:
                file.write(file1.read())
    print(' Reports written to ' + reportsDir + '/')


def getListOfFiles(dirName):
    '''Get the list of all files in directory tree at given path'''
    filePaths = []
    for (dirpath, _, filenames) in os.walk(dirName):
        filePaths += [os.path.join(dirpath, file) for file in filenames if file.endswith('.py')]
    return filePaths


def filePathsToStrings(filePaths):
    '''Reads the files indicates by filePaths into a list of strings'''
    strings = []
    for filePath in filePaths:
        with open(filePath, 'r') as file:
            strings.append(file.read().replace('\n', ''))
    return strings


if __name__ == '__main__':
    main()
