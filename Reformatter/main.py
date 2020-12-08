import argparse
import os
import re
import magic #Get Encoding of File

#Parsing CMD arguments
argparser = argparse.ArgumentParser(description='Reformat *.sng files to the standard Immanuel format.')
# input files
argparser.add_argument('files', nargs='+', help='Files to be reformatted. If directory, all *.sng files in it will be reformatted recursively.')

def cleanup(text):
    result = text
    result = re.sub(r'\n\s*\n', r'\n', result) #Remove empty lines
    result = re.sub(r'\n--\n', r'\n---\n', result) #Fix only 2 dashes for slide separation
    result = re.sub(r'\n---\n---\n', r'\n---\n', result) #Remove empty slides
    result = re.sub(r'\n---\n$', r'\n', result) # remove slide seperator at eof
    return result

def lineStartUppercase(matchobj): # Not used? TODO
    return matchobj.group(2).upper()

def formatLine(line):
    #Make character at line start uppercase
    line = re.sub(r'^\s*(#\d)?\s+([a-z])', lambda mobj: mobj.group(2).upper(), line) #Line start to upper case
    line = re.sub(r'[^\w\-"]$', r'', line) #Line end remove Symbols except quotes and dashes
    line = re.sub(r'[\'`]', r'\'', line) #Replace accents with apostrophes
    return line

def format(text):
    # we are in the file header
    inStart = True

    text = cleanup(text)

    result = ''
    for line in text.splitlines():
        if not inStart and '#FontSize=' in line: # FontSize is apparently used outside the header
            continue
        if inStart and not line == '---': # Don't change header
            result += line + '\n'
            continue
        inStart = False # With the first '---', we are out of the header
        result += formatLine(line) + '\n'
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
            f.write(format(f.read()))
    else:
        raise FileNotFoundError

for filename in argparser.parse_args().files:
    parse(filename)
