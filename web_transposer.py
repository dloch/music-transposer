from flask import Flask, request, make_response, render_template, redirect, send_from_directory, url_for
from uuid import uuid4
from bpmusictransposer.threadedworker import ThreadedWorker
import json
import os, atexit

def initialize(name):
    app = Flask(name)
    app.config['UPLOAD_FOLDER'] = os.environ.get('FLASK_UPLOAD_FOLDER', '/tmp')
    app.config['JOB_LIST'] = os.environ.get('JOB_LIST', 'job.list')
    with app.app_context():
        job_dir = app.config['UPLOAD_FOLDER']
        job_db = os.path.join(app.config['UPLOAD_FOLDER'], app.config['JOB_LIST'])
        app.worker = ThreadedWorker()
        app.worker.__configure__(job_dir, job_db)
        app.worker.start()
    cleanup = app.worker.CleanupClass([app.worker])
    atexit.register(cleanup.atexit)
    return app

app = initialize(__name__)

header = '<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>'

@app.route("/")
def docs():
    return "%s<div><h1>Functions</h1><ul><li>parse</li><ul><li>GET uuid</li><li>CREATE { file: file }</li></ul></ul></div>" % header

@app.get("/parse")
def parse_request_page():
    return render_template("form.html.jinja", page_js=url_for('static', filename='form.js'), **{ "results": app.worker.get_job_statuses() })

@app.post("/parse")
def new_parse_request():
    job_uuid = None
    try:
        f = request.files['to_parse']
        job_uuid = uuid4().hex
        save_result = f.save(os.path.join(app.config['UPLOAD_FOLDER'], job_uuid))
        app.worker.queue_job(job_uuid, f.filename)
    except Exception as e:
        return make_response(json.dumps({"result":"error"}), 500)
    return redirect("/parse/%s" % job_uuid, 302)

def get_parse_status(parse_uuid):
    if status := app.worker.get_job_status(parse_uuid):
        return status
    return {"status": "NA"}

@app.route("/parse/<string:parse_uuid>")
def parse_request_status(parse_uuid):
    if result := app.worker.get_job_status(parse_uuid):
        return render_template("waitpage.html.jinja", page_js=url_for('static', filename='waitpage.js'), **result)
    return make_response("Not found", 404)

@app.route("/parse/result/<string:parse_uuid>")
def get_parse_result(parse_uuid):
    if result := app.worker.get_job_status(parse_uuid):
        return json.dumps(result)
    return make_response("Not Found", 404)

@app.route("/parse/result/<string:parse_uuid>/file")
def get_parse_file(parse_uuid):
    if response := get_file(parse_uuid, "pdf"):
        return response
    return make_response("Not Found", 404)

@app.route("/parse/result/<string:parse_uuid>/source")
def get_parse_source(parse_uuid):
    if response := get_file(parse_uuid, "ly"):
        return response
    return make_response("Not Found", 404)

def get_file(parse_uuid, extension):
    if job_state := app.worker.get_job_status(parse_uuid):
        response_opts = {"download_name": "%s.%s" % (job_state['name'], extension)}
        response = send_from_directory(app.config['UPLOAD_FOLDER'], "%s.%s" % (parse_uuid, extension), **response_opts)
        return response
    return None
