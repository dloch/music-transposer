FROM dloch/lilypond:2.25.11


RUN dnf install -y python3-pip python3-flask && \
    dnf clean all

COPY dist/*.whl /work/

RUN pip install /work/* waitress

EXPOSE 8080

ENV FLASK_UPLOAD_FOLDER=/work 

ENTRYPOINT ["/usr/local/bin/waitress-serve"]
CMD ["bpmusictransposer.rest:app"]
