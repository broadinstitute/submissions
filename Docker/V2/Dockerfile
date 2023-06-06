FROM python:3.7-slim

COPY . .

COPY requirements.txt .
ADD requirements.txt
RUN pip3 install -r requirements.txt

ENV PYTHONPATH "/${PYTHONPATH}"

CMD ["/bin/bash"]