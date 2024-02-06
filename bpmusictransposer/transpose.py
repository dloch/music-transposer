import os, sys
from bpmusictransposer.musicgenerator import MusicGenerator
from bpmusictransposer.musicparser import MusicParser

def generate(tune, output):
    tunestr = MusicGenerator().from_tune(tune)
    with open(output, 'x') as file:
        file.write(tunestr)
    return tunestr

def parse(filename):
    with open(filename, 'r', encoding="cp1252") as file:
        tune = MusicParser.parsers['BagpipeMusicWriter'].get_tune(file.read())
    return tune

def main():
    toparse = sys.argv[1:]
    [generate(parse(filename), "%s.ly" % filename) for filename in toparse]
    return 0
