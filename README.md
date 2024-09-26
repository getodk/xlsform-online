# Overview
XLSForm Online is a Django-based web application that uses pyxform to convert a XLSForm to an ODK XForm and shows the preview of the Form in Enketo Express.

# Run locally

## Install requirements
* Python 3
* Java 8

```
pip install --requirement requirements.txt
export DJANGO_SECRET_KEY=<secret value>
export DJANGO_TMP_HOME=<location for temporary Forms>
export DJANGO_PERSISTENT_HOME=<location for permanent Forms>
python3 manage.py runserver
```

# Run in Docker
```
docker build --tag xlsform-online .
docker run --detach --publish 5001:80 xlsform-online
export DJANGO_SECRET_KEY=<secret value>
export DJANGO_TMP_HOME=<location for temporary Forms>
export DJANGO_PERSISTENT_HOME=<location for permanent Forms>
docker run -e DJANGO_SECRET_KEY=$DJANGO_SECRET_KEY -v $DJANGO_TMP_HOME:/tmp_home -v $DJANGO_PERSISTENT_HOME:/persistent_home -p 8000:8000 xlsform-online
```

# CORS

If you want to call `api/xlsform` from another application, please set the `CORS_ALLOWED_ORIGIN` value to the origin of that application in [`settings.py`](./xlsform_prj/settings.py)