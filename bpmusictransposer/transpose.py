import os, sys
from argparse import ArgumentParser
from bpmusictransposer.musicgenerator import MusicGenerator
from bpmusictransposer.musicparser import MusicParser
from bpmusictransposer.logger import Logger

def generate(tune, output, logger):
    # TODO: Allow selection of a generated type
    logger.log("Generate file %s" % output, 1)
    generator = MusicGenerator()
    generator.logger = logger
    tunestr = generator.from_tune(tune)
    with open(output, 'x') as file:
        file.write(tunestr)
    return tunestr

def parse(filename, logger):
    # TODO: Detect filetype and select the parser type
    parser = MusicParser.parsers['BagpipeMusicWriter']
    parser.logger = logger
    logger.log("Parse file %s" % filename, 1)
    with open(filename, 'r', encoding="cp1252") as file:
        tune = parser.get_tune(file.read())
    return tune

def parseargs():
    parser = ArgumentParser(
                    prog='Music Transposer',
                    description="Convert music files from one format into another"
                )
    parser.add_argument('-v', '--verbose',
                    action='count')
    parser.add_argument('filenames',
                    nargs='+')
    return parser.parse_args()

def main():
    arguments = parseargs()
    logger = Logger()
    logger.set_loglevel(int(arguments.verbose or 1))
    [generate(parse(filename, logger), "%s.ly" % filename, logger) for filename in arguments.filenames]
    return 0
