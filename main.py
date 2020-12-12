import argparse
import os
import re
import chardet

# Parsing CMD arguments
argparser = argparse.ArgumentParser(
    description='Reformat *.sng files to the standard Immanuel format.')
# input files
argparser.add_argument(
    'files', nargs='+',
    help='Files to be reformatted. If directory,\
    all *.sng files in it will be reformatted recursively.')
# output directory
argparser.add_argument(
    '-o', '--output-directory', dest='out',
    help='Write files in this output directory \
    instead of overwriting input files. Keeps directory structure')
# parse the args now to avoid unneeded execution of code
args = argparser.parse_args()


def cleanup(text):
    result = text
    result = re.sub(r'\n\s*\n', r'\n', result)  # Remove empty lines

    # Replace all unicode space characters with the default space
    # pattern: All horizontal whitespace characters except space
    result = re.sub(r'[^\S\n\v\f\r\u2028\u2029 ]', r' ', result)

    # Fix only 2 dashes for slide separation
    result = re.sub(r'\n--\n', r'\n---\n', result)

    result = re.sub(r'\n---\n---\n', r'\n---\n', result)  # Remove empty slides

    # remove slide seperator at eof
    result = re.sub(r'\n---\n$', r'\n', result)

    return result


def formatLine(line):
    # Make character at line start uppercase
    # Line start to upper case
    line = re.sub(r'^\s*(#\d)?\s+([a-z])',
                  lambda mobj: mobj.group(2).upper(), line)
    # Line end remove Symbols except quotes and dashes
    line = re.sub(r'[^\w\-"]$', r'', line)
    line = re.sub(r'[\'`´]', r'\'', line)  # Replace accents with apostrophes
    return line


def format(text):
    # we are in the file header
    inStart = True

    text = cleanup(text)

    result = ''
    for line in text.splitlines():
        # FontSize is apparently used outside the header
        if not inStart and '#FontSize=' in line:
            continue
        if inStart and not line == '---':  # Don't change header
            result += line + '\n'
            continue
        inStart = False  # With the first '---', we are out of the header
        result += formatLine(line) + '\n'
    return result


def parse(filename, outdir):
    if os.path.isdir(filename):  # if directory, parse subcontents recursively
        # if out is given and the directory does not exist in outdir, create it
        if outdir and not os.path.isdir(os.path.join(outdir, filename)):
            os.makedirs(os.path.join(outdir, filename))
        # recursively call parse for subdirectories
        for subfile in os.listdir(filename):
            # appending current filename -> don't change the working directory
            parse(filename + '/' + subfile, outdir)
    elif os.path.isfile(filename):
        raw = None
        with open(filename, 'rb') as infile:  # open binary -> encoding later
            raw = infile.read()
        # format decoded string (prevents empty files on error)
        formatted = format(raw.decode(chardet.detect(raw)['encoding']))
        # open file for writin (if necessary with outdir)
        with open(os.path.join(outdir, filename), 'w') as outfile:
            outfile.write(formatted)  # write out
    else:
        raise FileNotFoundError


# Set outdir
outdir = ''
if args.out:
    outdir = args.out

# Start parsing of files
for filename in args.files:
    parse(filename, outdir)
