import argparse
import os
import re
import chardet

# Parsing CMD arguments
argparser = argparse.ArgumentParser(
    description='Reformat *.sng files to the standard Immanuel format.')
# Input files
argparser.add_argument(
    'files', nargs='+',
    help='Files to be reformatted. If directory,\
    all *.sng files in it will be reformatted recursively.')
# Output directory
argparser.add_argument(
    '-o', '--output-directory', dest='out',
    help='Write files in this output directory \
    instead of overwriting input files. Keeps directory structure')
# Parse the args now to avoid unneeded execution of code
args = argparser.parse_args()


def cleanup(text):
    result = text
    # Remove empty lines
    result = re.sub(r'\n\s*\n', r'\n', result)
    # Replace all unicode space characters with the default space
    # Pattern: All horizontal whitespace characters except space
    result = re.sub(r'[^\S\n\v\f\r\u2028\u2029 ]', r' ', result)
    # Fix only 2 dashes for slide separation
    result = re.sub(r'\n--\n', r'\n---\n', result)
    # Remove empty slides
    result = re.sub(r'\n---\n---\n', r'\n---\n', result)
    # Remove slide seperator at eof
    result = re.sub(r'\n---\n$', r'\n', result)
    return result


def formatLine(line):
    # Make character at line start uppercase
    # Line start to upper case
    line = re.sub(r'^\s*(#\d)?\s+([a-z])',
                  lambda mobj: mobj.group(2).upper(), line)
    # Line end remove Symbols except quotes and dashes
    line = re.sub(r'[^\w\-"]$', r'', line)
    # Replace accents with apostrophes
    line = re.sub(r'[\'`´]', r'\'', line)
    return line


def format(text):
    # We are in the file header
    inStart = True

    text = cleanup(text)

    result = ''
    for line in text.splitlines():
        # FontSize is apparently used outside the header
        if not inStart and '#FontSize=' in line:
            continue
        # Don't change header
        if inStart and not line == '---':
            result += line + '\n'
            continue
        # With the first '---', we are out of the header
        inStart = False
        result += formatLine(line) + '\n'
    return result


def parse(filename, outdir):
    basename = os.path.basename(filename)
    if not basename:
        basename = os.path.basename(filename[:-1])

    # If directory, parse subcontents recursively
    if os.path.isdir(filename):
        # Create directory structure in outdir if present
        if outdir:
            os.makedirs(os.path.join(outdir, basename), exist_ok=True)

        # Recursively call parse for dir contents
        for subfile in os.listdir(filename):
            # Appending current filename -> don't change the working directory
            parse(os.path.join(filename, subfile),
                  os.path.join(outdir, basename))

    elif os.path.isfile(filename):
        # File must be .sng
        if not filename.endswith('.sng'):
            return

        # Read file contents
        raw = None
        # Open binary -> encoding later
        with open(filename, 'rb') as infile:
            raw = infile.read()

        # Format decoded string (prevents empty files on error)
        formatted = format(raw.decode(chardet.detect(raw)['encoding']))

        # Determine output filename
        outfilename = filename
        # If out is given and the directory does not exist in outdir, create it
        if outdir:
            # This file belongs in a subdir
            outfilename = os.path.join(outdir, basename)

        # If the file already exists, make it's filename the full filename
        i = 1
        pattern = outfilename[:-4] + r' ({})' + outfilename[-4:]
        while os.path.exists(outfilename):
            outfilename = pattern.format(i)
            i += 1

        # Open file for writing (if necessary with outdir)
        with open(outfilename, 'w') as outfile:
            outfile.write(formatted)  # write out

    else:
        raise FileNotFoundError


# Set outdir
outdir = ''
if args.out:
    outdir = args.out

# if the file already exists and is not a directory, throw error
if os.path.exists(outdir) and not os.path.isdir(outdir):
    raise FileExistsError
else:
    # otherwise create the dir
    os.makedirs(outdir, exist_ok=True)

# Start parsing of files
for filename in args.files:
    parse(filename, outdir)
