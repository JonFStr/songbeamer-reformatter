import argparse, os, re, chardet

#Parsing CMD arguments
argparser = argparse.ArgumentParser(description='Reformat *.sng files to the standard Immanuel format.')
# input files
argparser.add_argument('files', nargs='+', help='Files to be reformatted. If directory, all *.sng files in it will be reformatted recursively.')
# output directory
argparser.add_argument('-o', '--output-directory', dest='out', help='Write files in this output directory instead of overwriting input files. Keeps directory structure')
# parse the args now to avoid unneeded execution of code
args = argparser.parse_args()

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
    line = re.sub(r'[\'`´]', r'\'', line) #Replace accents with apostrophes
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

def parse(filename, outdir):
    if os.path.isdir(filename):     #if directory, parse subcontents recursively
        if outdir and not os.path.isdir(os.path.join(outdir, filename)): # if outdir is given and the directory does not exist in outdir, create it
            os.makedirs(os.path.join(outdir, filename))
        for subfile in os.listdir(filename): # recursively call parse for subdirectories
            parse(filename + '/' + subfile, outdir) #appending current filename for not having to change the working directory
    elif os.path.isfile(filename):
        raw = None
        with open(filename, 'rb') as infile: # open binary content to determine encoding later
            raw = infile.read()
        formatted = format(raw.decode(chardet.detect(raw)['encoding'])) # format decoded string (prevents empty files on error)
        with open(os.path.join(outdir, filename), 'w') as outfile: # open file for writin (if necessary with outdir)
            outfile.write(formatted) # write out
    else:
        raise FileNotFoundError

# Set outdir
outdir = ''
if args.out:
    outdir = args.out

# Start parsing of files
for filename in args.files:
    parse(filename, outdir)
