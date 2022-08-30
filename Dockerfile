FROM python:3

COPY . .

COPY requirements.txt .
RUN pip3 install -r requirements.txt

ENV PYTHONPATH "/${PYTHONPATH}"

CMD ["/bin/bash"]