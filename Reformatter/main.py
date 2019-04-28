import argparse
import os
argparser = argparse.ArgumentParser(description='Reformat *.sng files to the standard Immanuel format.')
argparser.add_argument('files', nargs='+', help='Files to be reformatted. If directory, all *.sng files in it will be reformatted recursively.')

def format(text):
    #TODO
    pass

def parse(filename):
    if os.path.isdir(filename):     #if directory, parse subcontents recursively
        for subfile in os.listdir(filename):
            parse(filename + '/' + subfile) #appending current filename for not having to change the working directory
    elif os.path.isfile(filename):
        with open(filename, 'r+', encoding='latin-1') as f:
            f.write(format(f.read()))
            pass
    else:
        raise FileNotFoundError

for filename in argparser.parse_args().files:
    parse(filename)
