FROM python:3.12.5-alpine

RUN apk --update add openjdk8-jre-base git

WORKDIR /usr/scr/app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

VOLUME ["/tmp_home", "/persistent_home"]

ENV DJANGO_TMP_HOME="/tmp_home"

ENV DJANGO_PERSISTENT_HOME="/persistent_home"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "xlsform_prj.wsgi:application"]