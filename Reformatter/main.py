import argparse
import os
import re
import magic #Get Encoding of File

#Parsing CMD arguments
argparser = argparse.ArgumentParser(description='Reformat *.sng files to the standard Immanuel format.')
argparser.add_argument('files', nargs='+', help='Files to be reformatted. If directory, all *.sng files in it will be reformatted recursively.')

#Regular Expressions
lineStartToUpper = r'^\s*(#\d)?\s*([a-zäöü])'
lineEndRmSymbols = r'\W$'
apostroph = r'[\'`]'

def lineStartUppercase(matchobj):
    return matchobj.group(2).upper()

def formatLine(line):
    #Make character at line start uppercase
    line = re.sub(lineStartToUpper, lineStartUppercase, line)
    line = re.sub(lineEndRmSymbols, '', line)
    line = re.sub(apostroph, '\'', line)
    return line

def cleanup(text):
    
    pass

def format(text):
    inStart = True
    result = ''
    for line in text.splitlines():
        if inStart and not line == '---':
            result += line + '\n'
            continue
        inStart = False
        if line == '':
            continue
        result += formatLine(line) + '\n'
        pass
    result = cleanup(result)
    return result

def determineCharset(filename):
    m = magic.Magic(mime_encoding = True)
    return m.from_file(filename)

def parse(filename):
    if os.path.isdir(filename):     #if directory, parse subcontents recursively
        for subfile in os.listdir(filename):
            parse(filename + '/' + subfile) #appending current filename for not having to change the working directory
    elif os.path.isfile(filename):
        with open(filename, 'r+', encoding=determineCharset(filename)) as f:
            print(format(f.read()))
            pass
    else:
        raise FileNotFoundError

for filename in argparser.parse_args().files:
    parse(filename)
