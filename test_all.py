import os
from bpmusictransposer.musicgenerator import MusicGenerator
from bpmusictransposer.bpparser import MusicParser

def cleanup(testdir, genfiletype):
    for file in filter(lambda x: x.endswith(genfiletype), os.listdir(testdir)):
        print("rm %s/%s" % (testdir, file))
        os.remove("%s/%s" % (testdir, file))

def write_tune(generator, tune, filename):
    print(filename)
    try:
        with open(filename, 'x') as file:
            tunestring = generator.from_tune(tune)
            file.write(tunestring)
    except Exception as e:
        raise e
        return (tune.title(), e)

def parse_tune(parser, filename):
    print("Parse %s" % filename)
    with open(filename) as file:
        tune = parser.get_tune(file.read())
    return tune

def __main__():
    filetype = "bww"
    filedir = "testdata"
    files = ['%s/%s' % (filedir, f) for f in filter(lambda x: x.endswith(filetype), os.listdir(filedir))]
    cleanup(filedir, 'ly')

    mp = MusicParser("BWW.v1.0.json")
    mg = MusicGenerator()
    tunes = [[parse_tune(mp, f), "%s.ly" % f] for f in files]
    print([write_tune(mg, tune[0], tune[1]) for tune in tunes])

if __name__ == '__main__':
    __main__()
