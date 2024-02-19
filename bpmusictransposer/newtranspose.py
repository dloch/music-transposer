import os, sys
from bpmusictransposer.musicgenerator import MusicGenerator
from bpmusictransposer.newmusicparser import MusicParser

def generate(tune, output):
    tunestr = MusicGenerator().from_tune(tune)
    with open(output, 'x') as file:
        file.write(tunestr)
    return tunestr

def parse(filename):
    parser = MusicParser.parsers["BagpipeMusicWriter"]
    tune = parser.get_tune_from_file(filename)
    return tune

def main():
    toparse = sys.argv[1:]
    [generate(parse(filename), "%s.ly" % filename) for filename in toparse]
    return 0
