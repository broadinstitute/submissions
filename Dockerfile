FROM python:3.8

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

ENV PYTHONPATH "/${PYTHONPATH}"

CMD ["/bin/bash"]