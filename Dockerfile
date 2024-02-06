FROM dloch/lilypond:2.25.11

COPY dist/*.whl /work/

RUN dnf install -y python3-pip python3-flask && \
    dnf clean all && \
    pip install /work/* waitress

EXPOSE 8080

ENV UPLOAD_FOLDER=/work 

ENTRYPOINT ["/usr/local/bin/waitress-serve", "bpmusictransposer.rest:app"]
