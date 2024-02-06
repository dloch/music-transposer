import os, sys
from bpmusictransposer.musicgenerator import MusicGenerator
from bpmusictransposer.musicparser import MusicParser

def cleanup(testdir, genfiletype):
    for file in filter(lambda x: x.endswith(genfiletype), os.listdir(testdir)):
        os.remove("%s/%s" % (testdir, file))

def write_tune(generator, tune, filename):
    try:
        tunestring = generator.from_tune(tune)
        with open(filename, 'x') as file:
            file.write(tunestring)
    except Exception as e:
        print("%s Error in %s" % (e, filename), file=sys.stderr)

def parse_tune(parser, filename):
    try:
        tunestr = ""
        with open(filename, 'r', encoding="cp1252") as file:
            tunestr = file.read()
        return parser.get_tune(tunestr)
    except:
        print("Parse %s failed" % filename)
        return None

def __main__():
    filetype = "bww"
    filedir = "testdata"
    files = ['%s/%s' % (filedir, f) for f in filter(lambda x: x.endswith(filetype), os.listdir(filedir))]
    cleanup(filedir, 'ly')

    mp = MusicParser.parsers["BagpipeMusicWriter"]
    mg = MusicGenerator()
    tunes = [[parse_tune(mp, f), "%s.ly" % f] for f in files]
    [write_tune(mg, tune[0], tune[1]) for tune in tunes]

if __name__ == '__main__':
    __main__()
