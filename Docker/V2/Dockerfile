FROM python:3.8-slim

COPY . .
# COPY requirements.txt .
ADD requirements.txt .
RUN pip3 install -r requirements.txt

ENV PYTHONPATH "/${PYTHONPATH}"

CMD ["/bin/bash"]