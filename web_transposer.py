from flask import Flask, request, make_response, render_template, redirect, send_from_directory
from uuid import uuid4
import json
from queue import SimpleQueue
from bpmusictransposer.musicparser import MusicParser
from bpmusictransposer.musicgenerator import MusicGenerator
from threading import Thread
import sys, os, atexit, time, subprocess

def doWork():
    """Continuously take tasks off the queue, convert them to .ly format, generate the pdf, then make them available"""
    # TODO: Worker queue to clean them up afterwards
    mp = MusicParser("./parserdefs/BWW.v1.0.json")
    mg = MusicGenerator()
    db_file = os.path.join(app.config['UPLOAD_FOLDER'], app.config['JOB_LIST'])
    while app.is_running:
        try:
            jobid = app.parse_promises.get(timeout=15)
            filename = os.path.join(app.config['UPLOAD_FOLDER'], jobid)
            print("Processing %s" % jobid)
            db_format = "\n%s" if os.path.exists(db_file) else "%s"
            original_name = app.parse_requests[jobid]["name"]
            with open(db_file, 'a') as file:
                file.write(db_format % json.dumps({"uuid": jobid, "name": original_name}))
            # Wait 20s for the file to save:
            for x in range(0, 20):
                time.sleep(1.5)
                if os.path.isfile(filename):
                    break
            try:
                app.parse_requests[jobid] = { "status": "Processing", "name": original_name }
                with open(filename) as file:
                    tunestr = file.read()
                os.unlink(filename)
                tune = mp.get_tune(tunestr)
                resultstr = mg.from_tune(tune)
                with open(filename, 'x') as file:
                    file.write(resultstr)
                print("Completed internal processing of %s" % filename)
                result = subprocess.run(["/usr/bin/lilypond", "-o", filename, filename]).check_returncode()
                app.completed_requests[jobid] = app.parse_requests[jobid]["name"]
                print("Completed processing of %s" % jobid)
                app.parse_requests[jobid] = { "status": "Complete", "name": original_name }
            except Exception as e:
                print("Worker Exception")
                print(e, file=sys.stderr)
                if os.path.isfile(filename):
                    os.unlink(filename)
        except Exception as e:
            # Do nothing
            pass

class CleanupClass:
    def atexit(self):
        app.is_running = False
        for worker in self.workers:
            worker.join()
        for (jobid, state) in self.app.parse_requests.items():
            print("Cancel job: %s, %s" % (jobid, state))

    def __init__(self, app, workers):
        self.app = app
        self.workers = workers

def load_requests(app):
    job_list = os.path.join(app.config['UPLOAD_FOLDER'], app.config['JOB_LIST'])
    if not os.path.exists(job_list):
        return
    with open(os.path.join(app.config["UPLOAD_FOLDER"], app.config['JOB_LIST']), 'r') as dbfile:
        jobs = map(json.loads, dbfile.readlines())
    for job in jobs:
        app.completed_requests[job["uuid"]] = job["name"]

def initialize(name):
    app = Flask(name)
    app.config['UPLOAD_FOLDER'] = os.environ.get('FLASK_UPLOAD_FOLDER', '/tmp')
    app.config['JOB_LIST'] = os.environ.get('JOB_LIST', 'job.list')
    with app.app_context():
        app.is_running = True
        app.parse_requests = {}
        app.parse_promises = SimpleQueue()
        app.completed_requests = {}
        load_requests(app)
        app.worker_thread = Thread(target=doWork)
        app.worker_thread.start()
    cleanup = CleanupClass(app, [app.worker_thread])
    atexit.register(cleanup.atexit)
    return app

app = initialize(__name__)

header = '<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>'

@app.route("/")
def docs():
    return "%s<div><h1>Functions</h1><ul><li>parse</li><ul><li>GET uuid</li><li>CREATE { file: file }</li></ul></ul></div>" % header

@app.get("/parse")
def parse_request_page():
    return render_template("form.html.jinja", **{ "results": app.completed_requests })

@app.post("/parse")
def new_parse_request():
    parse_uuid = None
    try:
        f = request.files['to_parse']
        parse_uuid = uuid4().hex
        app.parse_requests[parse_uuid] = { "status": "Queued", "name": request.files['to_parse'].filename }
        save_result = f.save('/tmp/%s' % parse_uuid)
        app.parse_promises.put(parse_uuid, timeout=5)
    except Exception as e:
        return make_response(json.dumps({"result":"error"}), 400)
    return redirect("/parse/%s" % parse_uuid, 302)

def get_parse_status(parse_uuid):
    if parse_uuid in app.completed_requests:
        return {"uuid": parse_uuid, "status": "Complete"}
    elif parse_uuid in app.parse_requests:
        result = app.parse_requests[parse_uuid]
        result["uuid"] = parse_uuid
        return result
    return {"status": "NA"}

@app.route("/parse/<string:parse_uuid>")
def parse_request_status(parse_uuid):
    result = get_parse_status(parse_uuid)
    if "uuid" in result:
        return render_template("waitpage.html.jinja", **get_parse_status(parse_uuid))
    return make_response("Not found", 404)

@app.route("/waitpage.js")
def waitpage_js():
    return render_template("waitpage.js.jinja")

@app.route("/parse/result/<string:parse_uuid>")
def get_parse_result(parse_uuid):
    result = get_parse_status(parse_uuid)
    if "uuid" in result:
        return json.dumps(result)
    return make_response("Not Found", 404)

@app.route("/parse/result/<string:parse_uuid>/file")
def get_parse_file(parse_uuid):
    if parse_uuid in app.completed_requests:
        response_opts = {"download_name": "%s.pdf" % app.completed_requests[parse_uuid], "mimetype": "application/pdf"}
        response = send_from_directory(app.config['UPLOAD_FOLDER'], "%s.pdf" % parse_uuid, **response_opts)
        response.direct_passthrough = False
        return response
    return make_response("Not Found", 404)

@app.route("/parse/result/<string:parse_uuid>/source")
def get_parse_source(parse_uuid):
    if parse_uuid in app.completed_requests:
        response_opts = {"download_name": "%s.ly" % app.completed_requests[parse_uuid]}
        response = send_from_directory(app.config['UPLOAD_FOLDER'], parse_uuid, **response_opts)
        response.direct_passthrough = False
        return response
    return make_response("Not Found", 404)
