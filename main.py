import argparse
import os
import re
import chardet
import unicodedata

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
# verbose mode
argparser.add_argument(
    '-v', '--verbose', dest='verbose', action='store_true',
    help='Verbose output'
)
# Parse the args now to avoid unneeded execution of code
args = argparser.parse_args()

# ANSI control sequences
ctrl_clearLine = '\x1b[K'
ctrl_moveUp = '\x1b[1A'


# Log message depending on verbosity & args
def log(*message, level='l'):
    if (level != 'l') and (level == 'v' and not args.verbose):
        return
    print(ctrl_moveUp + message[0], *message[1:], end=ctrl_clearLine+'\n\n')


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
    # Replace Unicode sequences (i.e. a + ̈  = ̈a)
    # with their legacy equivalent (i.e. ä)
    result = unicodedata.normalize('NFC', result)
    return result


def formatLine(line):
    # Make character at line start uppercase
    # Line start to upper case
    line = re.sub(r'^\s*(#\d\s+)?([a-z])',
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


def determine_encoding(raw):
    # Detect all possible encodings and select one from predefined list
    possible_encodings = chardet.detect_all(raw)
    log(possible_encodings, level='v')

    # Iterate over found encodings
    for possible_enc in possible_encodings:
        # Take encoding from dictionary
        encoding = possible_enc['encoding']
        if not encoding:
            continue
        encoding = encoding.lower()
        # Second loop is necessary because of possible amendments
        for allowed_enc in ['iso-8859-1', 'windows-1252', 'utf-8', 'utf-16', 'utf-32', 'ascii']:
            # Check if the found encoding name starts with an allowed one
            if allowed_enc in encoding:
                return possible_enc['encoding']
    raise ValueError('Cannot detect matching encoding')


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
          end=ctrl_clearLine + '\n')

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
            encoding = determine_encoding(raw)
            contents = raw.decode(encoding)
        except (ValueError, AttributeError) as err:
            log('Error decoding file "' + filename + '":', err)
            return

        # Format decoded string (prevents empty files on error)
        formatted = format(contents)

        # Determine output filename
        outfilename = filename
        # If custom out is given, put it in there
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

        # Write formatted file in windows encoding & line ending
        with open(outfilename, 'w', encoding='windows-1252', newline='\r\n') as outfile:
            try:
                outfile.write(formatted)
            except UnicodeEncodeError as err:
                log('Error encoding reformatted file "' + outfilename + '":', err)

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
