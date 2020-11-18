from difflib import SequenceMatcher
import itertools
import os
import pathlib
import pprint

def main():
    NUMBER_OF_TOP_RESULTS = 20
    REPORTS_DIR = 'reports'
    dirName = './';

    # Get the list of all files in directory tree at given path
    listOfFiles = list()
    for (dirpath, _, filenames) in os.walk(dirName):
        listOfFiles += [os.path.join(dirpath, file) for file in filenames if file.endswith('.c')]

    # Read all files into a list of strings
    fileStrings = list()
    for filePath in listOfFiles:
        with open(filePath, 'r') as file:
            fileStrings.append(file.read().replace('\n', ''))

    print("Comparing", len(listOfFiles), "files...", end='', flush=True)

    # Create a list of tuples (ratio, filePath0, filePath1)
    ratios = list()
    for i, j in itertools.combinations(range(len(fileStrings)), 2):
#        ratio = SequenceMatcher(None, fileStrings[i], fileStrings[j]).ratio()
        ratio = SequenceMatcher(lambda c: c.isspace(), fileStrings[i], fileStrings[j]).ratio()
        tup = ratio, listOfFiles[i], listOfFiles[j]
        ratios.append(tup)
    print(' Done')

    # Sort to find the files which are most similar
    print('Sorting ratios...', end='', flush=True)
    ratios.sort(reverse=True)
    bestMatches = ratios[0:NUMBER_OF_TOP_RESULTS]
    print(' Done')

    print('Showing the ' + str(NUMBER_OF_TOP_RESULTS) + ' best matches:')
    pp = pprint.PrettyPrinter(width=200)
    pp.pprint(bestMatches)

    # Generate report
    print('Generating reports...', end='', flush=True)
    separator = '\n' + '-' * 80 + '\n'
    pathlib.Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    for idx, (ratio, filePath0, filePath1) in enumerate(bestMatches):
        with open(REPORTS_DIR + '/' + str(idx) + '.txt', 'w') as file:
            file.write('Match ratio: ' + str(ratio) + '\n')
            file.write('File 0: ' + filePath0 + '\n')
            file.write('File 1: ' + filePath1 + '\n')
            file.write(separator)
            with open(filePath0, 'r') as file0:
                file.write(file0.read())
            file.write(separator)
            with open(filePath1, 'r') as file1:
                file.write(file1.read())
    print(' Reports written to ' + REPORTS_DIR + '/')


if __name__ == '__main__':
    main()
