FROM python:3.9
COPY . /app
WORKDIR /app
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5001 
ENTRYPOINT [ "python" ] 
CMD [ "app.py" ] 
