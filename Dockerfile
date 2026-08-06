FROM python:3.13.14-alpine AS build
RUN apk --update --no-cache add git
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

 
FROM python:3.13.14-alpine AS runtime
WORKDIR /usr/src/app
RUN apk --update --no-cache add openjdk8-jre-base
COPY --from=build /usr/local /usr/local
COPY . .
EXPOSE 8000
VOLUME ["/tmp_home", "/persistent_home"]
ENV DJANGO_TMP_HOME="/tmp_home"
ENV DJANGO_PERSISTENT_HOME="/persistent_home"
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "5", "--timeout", "600", "--max-requests", "25", "--max-requests-jitter", "5", "xlsform_prj.wsgi:application"]
