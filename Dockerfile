FROM amd64/python:3.7.3-alpine

WORKDIR /lovherk

COPY requirements.txt ./

RUN python3 -m pip install -r requirements.txt

COPY . .

CMD ["python3", "lovherk.py"]