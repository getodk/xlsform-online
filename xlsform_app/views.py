# Create your views here.
from django.http import HttpResponse
from django.http import JsonResponse
from django.http import HttpResponseBadRequest
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django import forms
from django.conf import settings
from enum import Enum
import shutil

import tempfile
import os
import json
import codecs
import re
import uuid

import pyxform
from pyxform import xls2json
from pyxform.utils import has_external_choices
from pyxform.xls2json_backends import sheet_to_csv
from pyxform.validators import odk_validate

DJANGO_TMP_HOME = os.environ['DJANGO_TMP_HOME']
DJANGO_PERSISTENT_HOME = os.environ['DJANGO_PERSISTENT_HOME']

class UploadFileForm(forms.Form):
    file = forms.FileField(attrs={ 'accept': '.xls, .xlsx' })

class PreviewTarget(Enum):
    WEB_FORMS = 'web-forms'
    ENKETO = 'enketo'

def clean_name(name):

    # name will be used in a URL and # and , aren't valid characters
    return re.sub("#|,","", name)

def append_cors_headers(request, response):
    allowed_origin = settings.CORS_ALLOWED_ORIGIN
    if(allowed_origin):
        origin_list = [item.strip() for item in allowed_origin.split(",")]
        request_origin = request.META.get('HTTP_ORIGIN')
        if(request_origin in origin_list):
            response["Access-Control-Allow-Origin"] = request_origin
            response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

def handle_uploaded_file(file, directory): 
    
    filename = clean_name(file.name)

    filepath = os.path.join(directory, filename)
    destination = open(filepath, 'wb+')
    for chunk in file.chunks():
        destination.write(chunk)
    destination.close()
    return filepath

def copy_file(directory, file_path):
    if not (os.access(directory, os.F_OK)):
        os.makedirs(directory)
    return shutil.copy(file_path, directory)


def convert_xlsform(file, baseDownloadUrl, preview_target):
    error = None
    warnings = None

    filename, ext = os.path.splitext(file.name)

    filename = clean_name(filename)

    if not (os.access(DJANGO_TMP_HOME, os.F_OK)):
        os.mkdir(DJANGO_TMP_HOME)

    #Make a randomly generated directory to prevent name collisions
    dir_uuid = uuid.uuid4().hex
    temp_dir = tempfile.mkdtemp(prefix=dir_uuid, dir=DJANGO_TMP_HOME)
    relpath_itemsets_csv = None

    # Subdirectory i.e. 'web-form' / 'enketo' is inferred by the source  
    # api_xlsform is called only by Web Form Preview and the view (upload.html) has only option to view Form in Enketo
    permanent_dir = os.path.join(DJANGO_PERSISTENT_HOME, preview_target.value, dir_uuid)
    if not (os.access(permanent_dir, os.F_OK)):
        os.makedirs(permanent_dir)

    try:
        if ext == '.xml':
            permanent_file_path = handle_uploaded_file(file, permanent_dir)

            # We need to copy the file to temp_dir so that it can be served via `download()`
            xml_path = copy_file(temp_dir, permanent_file_path)
            relpath = os.path.relpath(xml_path, DJANGO_TMP_HOME)
            warnings = odk_validate.check_xform(xml_path)
        else:
            xml_path = os.path.join(temp_dir, filename + '.xml')
            relpath = os.path.relpath(xml_path, DJANGO_TMP_HOME)

            #Init the output xml file.
            fo = open(xml_path, "wb+")
            fo.close()

            #TODO: use the file object directly
            xls_path = handle_uploaded_file(file, permanent_dir)

            warnings = []
            json_survey = xls2json.parse_file_to_json(xls_path, warnings=warnings)
            survey = pyxform.create_survey_element_from_dict(json_survey)
            survey.print_xform_to_file(xml_path, warnings=warnings, pretty_print=False)

            if has_external_choices(json_survey):
                # Create a csv for the external choices
                itemsets_csv = os.path.join(os.path.split(xml_path)[0],
                                            "itemsets.csv")
                choices_exported = sheet_to_csv(xls_path, itemsets_csv,
                                                "external_choices")
                if not choices_exported:
                    warnings += ["Could not export itemsets.csv, "
                                    "perhaps the external choices sheet is missing."]
                else:
                    relpath_itemsets_csv = os.path.relpath(itemsets_csv, DJANGO_TMP_HOME)
    except Exception as e:
        error = 'Error: ' + str(e)

    return { 
        'xform_url':  None if not relpath else baseDownloadUrl + relpath,
        'itemsets_url': None if not relpath_itemsets_csv else baseDownloadUrl + relpath_itemsets_csv, 
        'error': error,
        'warnings': warnings
    }

@xframe_options_exempt
def index(request):
    if request.method == 'POST':  # If the form has been submitted...
        form = UploadFileForm(request.POST, request.FILES)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass

            conversion_result = convert_xlsform(request.FILES['file'], request.build_absolute_uri('./downloads/'), PreviewTarget.ENKETO)

            return render(request, 'upload.html', {
                'form': UploadFileForm(),
                'xml_path': conversion_result.get('xform_url'),
                'xml_url': conversion_result.get('xform_url'),
                'itemsets_url': conversion_result.get('itemsets_url'),
                'success': not conversion_result.get('error'),
                'error': conversion_result.get('error'),
                'warnings': conversion_result.get('warnings'),
                'result': True,
            })
    else:
        form = UploadFileForm()  # An unbound form

    return render(request, 'upload.html', context={
        'form': form,
    })

@xframe_options_exempt
def serve_file(request, path):
    path = path.strip("/")
    path_segments = path.split("/")
    if len(path_segments) == 2 and all(segment not in (".", "..", "") for segment in path_segments):
        fo = codecs.open(os.path.join(DJANGO_TMP_HOME, path), mode='r', encoding='utf-8')
        data = fo.read()
        fo.close()
        response = HttpResponse(content_type='application/xml')
        response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(os.path.normpath(path))
        response.write(data)

        append_cors_headers(request, response)

        return response

@csrf_exempt
def api_xlsform(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    conversion_result = convert_xlsform(request.FILES['file'],request.build_absolute_uri('/downloads/'), PreviewTarget.WEB_FORMS)

    response = JsonResponse(conversion_result)
    
    append_cors_headers(request, response)

    return response