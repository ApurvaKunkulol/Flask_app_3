FROM python:3.6.9
COPY . ../Flask_app_3
WORKDIR ../Flask_app_3
RUN pip install -r requirements.txt
ENTRYPOINT ["python"]
CMD ["./app.py"]