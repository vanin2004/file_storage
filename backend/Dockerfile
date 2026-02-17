FROM python:3.12-alpine

RUN mkdir -p /backend

WORKDIR /backend

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python",  "-m", "src.app"]

# CMD ["tail", "-f", "/dev/null"]