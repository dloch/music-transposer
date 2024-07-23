import os, sys, datetime, traceback
from multiprocess import Pool
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
        return (parser.get_tune_from_file(filename), "%s.ly"  % filename)
    except Exception as e:
        print("Parse %s failed: %s" % (filename, e))
        return None

def __main__():
    filetype = "bww"
    filedir = "testdata"
    files = ['%s/%s' % (filedir, f) for f in filter(lambda x: x.endswith(filetype), os.listdir(filedir))]
    cleanup(filedir, 'ly')

    mp = MusicParser.parsers["BagpipeMusicWriter"]
    mg = MusicGenerator()
    start = datetime.datetime.now()
    #with Pool(processes=8) as pool:
        #tunes = [pool.apply_async(parse_tune, (mp, f)) for f in files]
        #tunes = [x.get() for x in tunes]
    tunes = [parse_tune(mp, f) for f in files]
    time_elapsed = datetime.datetime.now() - start
    print("Took %s to parse" % time_elapsed)
    start = datetime.datetime.now()
    [write_tune(mg, tune[0], tune[1]) for tune in tunes]
    time_elapsed = datetime.datetime.now() - start
    print("Took %s to generate" % time_elapsed)

if __name__ == '__main__':
    __main__()
