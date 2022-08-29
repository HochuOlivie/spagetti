import sys

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def printError(msg):
    print(f"{bcolors.FAIL}[ERROR] {msg}{bcolors.ENDC}")

def printWarning(msg):
    print(f"{bcolors.WARNING}[WARNING] {msg}{bcolors.ENDC}")

def printSuccess(msg):
    print(f"{bcolors.OKGREEN}{msg}{bcolors.ENDC}")

def fatalError(msg):
    printError(msg)
    sys.exit()