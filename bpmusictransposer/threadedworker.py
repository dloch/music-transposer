from threading import Thread, get_ident
from bpmusictransposer.musicgenerator import MusicGenerator
from bpmusictransposer.musicparser import MusicParser
from queue import SimpleQueue
from uuid import uuid4
import os, json, time, sys, subprocess

class ThreadedWorker(Thread):
    # TODO: Add reprocessing of failed job option
    # TODO: Allow combining matching source files (And results) when they happen
    work_queue = SimpleQueue()
    is_running = True
    parse_status = {}

    def run(self):
        """Continuously take tasks off the queue, convert them to .ly format, generate the pdf, then make them available"""
        # TODO: Worker queue to clean them up afterwards
        mp = MusicParser.parsers["BagpipeMusicWriter"]
        mg = MusicGenerator()
        while self.is_running:
            try:
                print("%d: Checking queue" % get_ident())
                jobid = self.work_queue.get(timeout=15)
                filename = os.path.join(self.job_dir, jobid)
                print("%d: Processing %s" % (get_ident(), jobid))
                # Wait 20s for the file to save:
                for x in range(0, 20):
                    print("%d: Waiting on file available" % get_ident())
                    time.sleep(1.5)
                    if os.path.isfile(filename):
                        print("%d: File available" % get_ident())
                        break
                print("%d: Process %s" % (get_ident(), jobid))
                try:
                    self.set_job_status(jobid, { "status": "Processing" })
                    with open(filename) as file:
                        tunestr = file.read()
                    os.unlink(filename)
                    tune = mp.get_tune(tunestr)
                    resultstr = mg.from_tune(tune)
                    with open("%s.ly" % filename, 'x') as file:
                        file.write(resultstr)
                    print("%d: Completed internal processing of %s" % (get_ident(), filename))
                    result = subprocess.run(["/usr/bin/lilypond", "-o", filename, "%s.ly" % filename]).check_returncode()
                    print("%d: Completed processing of %s" % (get_ident(), jobid))
                    self.set_job_status(jobid, { "status": "Complete" })
                    self.write_jobdb()
                except Exception as e:
                    print("%d: Worker Exception" % get_ident())
                    print(e, file=sys.stderr)
                    self.set_job_status(jobid, {"status": "Failed" })
                    self.write_jobdb()
                    if os.path.isfile(filename):
                        print("%d: Leaving %s" % (get_ident(), filename))
                        #os.unlink(filename)
            except Exception as e:
                # Do nothing
                pass

    def write_jobdb(self):
        # TODO: Be more efficient than this
        with open(self.job_db, 'w') as dbfile:
            dbfile.truncate(0)
            dbfile.write(json.dumps(self.parse_status))
    
    def set_job_status(self, uuid, update):
        self.parse_status[uuid].update(update)

    def get_job_status(self, uuid):
        if uuid in self.parse_status:
            return self.parse_status[uuid]
        return None

    def get_job_statuses(self):
        return [x for x in self.parse_status.values()]

    def queue_job(self, uuid, filename):
        self.parse_status[uuid] = { "status": "Queued", "name": filename, "uuid": uuid }
        print("Add %s to worker")
        self.work_queue.put(uuid, timeout=5)
        print("Added")

    class CleanupClass:
        def atexit(self):
            for worker in self.workers:
                worker.is_running = False
                worker.join()
            for (jobid, state) in [item for item in worker.parse_status.items() for worker in self.workers]:
                print("Cancel job: %s, %s" % (jobid, state))

        def __init__(self, workers):
            self.workers = workers

    def load_requests(self, job_db):
        job_list = job_db
        if not os.path.exists(job_list):
            return
        with open(job_db, 'r') as dbfile:
            self.parse_status.update(json.loads(dbfile.read()))

    def __configure__(self, job_dir, dbfile):
        self.job_dir = job_dir
        self.job_db = dbfile
        self.load_requests(dbfile)
