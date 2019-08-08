FROM python:3 as python-base
COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3-slim

COPY requirements.txt /opt/kfailb/requirements.txt
WORKDIR /opt/kfailb
COPY --from=python-base /root/.cache /root/.cache

RUN useradd toor
RUN pip install -r requirements.txt && rm -rf /root/.cache

COPY kfailb/* /opt/kfailb/

USER toor
ENV PYTHONPATH="$PYTHONPATH:/opt/"
CMD ["python3", "cmd.py"]
