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
# overwrite files in output directory
argparser.add_argument(
    '-f', '--overwrite', dest='overwrite', action='store_true',
    help='Overwrite files in the output directory, if they are already present'
)
# Parse the args now to avoid unneeded execution of code
args = argparser.parse_args()

# ANSI control sequences
ctrl_clearLine = '\x1b[K'
ctrl_moveUp = '\x1b[1A'


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
    # Remove backslashes
    line = line.replace('\\', '')
    # Line end remove Symbols except quotes and dashes
    line = re.sub(r'[^\w\-"]$', r'', line)
    # Replace accents with apostrophes
    line = re.sub(r'[\'`´]', "'", line)
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
    global fileCounter, fileSum

    # status line (first sequence moves cursor up)
    fileCounter += 1

    # number of files over total files and percentage
    stats = f'{{count: >{len(f"{fileSum:,}")},}} of {fileSum:,} ({{percent}}%)'
    stats = stats.format(count=fileCounter,
                         percent=round(fileCounter/fileSum*100)
                         if fileSum != 0 else 0)

    # print rewriting status line
    print(ctrl_moveUp + 'Reformatting:', stats, filename,
          end=ctrl_clearLine+'\n')

    # set the basename (not found by function if string ands with /)
    basename = os.path.basename(filename)
    if not basename:
        basename = os.path.basename(filename[:-1])

    # If directory, parse subcontents recursively
    if os.path.isdir(filename):
        # If custom out given, append this directory to it
        if outdir:
            outdir = os.path.join(outdir, basename)

        # Recursively call parse for dir contents
        subfiles = os.listdir(filename)
        fileSum += len(subfiles)  # update total sum of files
        for subfile in subfiles:
            # Appending current filename -> don't change the working directory
            parse(os.path.join(filename, subfile), outdir)

    elif os.path.isfile(filename):
        # File must be .sng
        if not filename.endswith('.sng'):
            return

        # Open binary -> encoding later
        with open(filename, 'rb') as infile:
            raw = infile.read()

        # decode string
        try:
            encoding = chardet.detect(raw)['encoding']
            if not encoding:
                raise ValueError('Cannot detect matching encoding')
            contents = raw.decode(encoding)
        except ValueError as err:
            print(ctrl_moveUp + 'Error decoding file "' + filename + '":', err,
                  end='\n\n')
            return

        # Format decoded string (prevents empty files on error)
        formatted = format(contents)

        # Determine output filename
        outfilename = filename
        # if custom out is given, put it in there
        if outdir:
            # This file belongs in a subdir
            outfilename = os.path.join(outdir, basename)
            # If the file already exists in custom outdir
            # and overwrite is not specified, append number
            if not args.overwrite:
                i = 1
                # Pattern to insert number before .sng
                pattern = outfilename[:-4] + r' ({})' + outfilename[-4:]
                while os.path.exists(outfilename):
                    outfilename = pattern.format(i)
                    i += 1

        # Create needed directories for this file
        os.makedirs(os.path.dirname(outfilename), exist_ok=True)

        # Write formatted file
        with open(outfilename, 'w') as outfile:
            outfile.write(formatted)

    else:
        raise FileNotFoundError


# Set outdir
outdir = ''
if args.out:
    outdir = args.out

# If the file already exists and is not a directory, throw error
if os.path.exists(outdir) and not os.path.isdir(outdir):
    raise FileExistsError
else:
    # Otherwise create the dir
    os.makedirs(outdir, exist_ok=True)

# one empty line to let the cursor move up in the status line
print()

# set initial file sum for status line
fileSum = len(args.files)
fileCounter = 0

# Start parsing of files
for filename in args.files:
    parse(filename, outdir)
