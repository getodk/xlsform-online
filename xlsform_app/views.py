# Create your views here.
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.shortcuts import render
from django import forms

import tempfile
import os
import json
import codecs

import pyxform
from pyxform import xls2json
from pyxform.utils import sheet_to_csv, has_external_choices

DJANGO_TMP_HOME = os.environ['DJANGO_TMP_HOME']

class UploadFileForm(forms.Form):
    file = forms.FileField()


def handle_uploaded_file(f, temp_dir): 
    
    # filename will be used in a URL and # isn't a valid character
    filename = f.name.replace("#","")

    xls_path = os.path.join(temp_dir, filename)
    destination = open(xls_path, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    return xls_path


def json_workbook(request):
    error = None
    warningsList = []

    if not (os.access(DJANGO_TMP_HOME, os.F_OK)):
        os.mkdir(DJANGO_TMP_HOME)

    #Make a randomly generated directory to prevent name collisions
    temp_dir = tempfile.mkdtemp(prefix='', dir=DJANGO_TMP_HOME)
    form_name = request.POST.get('name', 'form')
    output_filename = form_name + '.xml'
    out_path = os.path.join(temp_dir, output_filename)
    if os.access(out_path, os.F_OK):
        os.remove(out_path)
    try:
        json_survey = xls2json.workbook_to_json(json.loads(request.POST['workbookJson']), form_name=form_name,
                                                warnings=warningsList)
        survey = pyxform.create_survey_element_from_dict(json_survey)
        survey.print_xform_to_file(out_path, warnings=warningsList, pretty_print=False)
    except Exception as e:
        error = str(e)
    return HttpResponse(json.dumps({
                                       'dir': os.path.split(temp_dir)[-1],
                                       'name': output_filename,
                                       'error': error,
                                       'warnings': warningsList,
                                   }, indent=4), mimetype="application/json")

@xframe_options_exempt
def index(request):
    if request.method == 'POST':  # If the form has been submitted...
        form = UploadFileForm(request.POST, request.FILES)  # A form bound to the POST data
        if form.is_valid():  # All validation rules pass

            error = None
            warnings = None

            filename, ext = os.path.splitext(request.FILES['file'].name)

            # filename will be used in a URL and # isn't a valid character
            filename = filename.replace("#","")

            if not (os.access(DJANGO_TMP_HOME, os.F_OK)):
                os.mkdir(DJANGO_TMP_HOME)

            #Make a randomly generated directory to prevent name collisions
            temp_dir = tempfile.mkdtemp(prefix='', dir=DJANGO_TMP_HOME)
            xml_path = os.path.join(temp_dir, filename + '.xml')
            itemsets_url = None

            relpath = os.path.relpath(xml_path, DJANGO_TMP_HOME)

            #Init the output xml file.
            fo = open(xml_path, "wb+")
            fo.close()

            try:
                #TODO: use the file object directly
                xls_path = handle_uploaded_file(request.FILES['file'], temp_dir)
                warnings = []
                json_survey = xls2json.parse_file_to_json(xls_path, warnings=warnings)
                survey = pyxform.create_survey_element_from_dict(json_survey)
                survey.print_xform_to_file(xml_path, warnings=warnings, pretty_print=False)

                if has_external_choices(json_survey):
                    # Create a csv for the external choices
                    itemsets_csv = os.path.join(os.path.split(xls_path)[0],
                                                "itemsets.csv")
                    relpath_itemsets_csv = os.path.relpath(itemsets_csv, DJANGO_TMP_HOME)
                    choices_exported = sheet_to_csv(xls_path, itemsets_csv,
                                                    "external_choices")
                    if not choices_exported:
                        warnings += ["Could not export itemsets.csv, "
                                     "perhaps the external choices sheet is missing."]
                    else:
                        itemsets_url = request.build_absolute_uri('./downloads/' + relpath_itemsets_csv)
            except Exception as e:
                error = 'Error: ' + str(e)

            return render(request, 'upload.html', {
                'form': UploadFileForm(),
                'xml_path': request.build_absolute_uri('./downloads/' + relpath),
                'xml_url': request.build_absolute_uri('./downloads/' + relpath),
                'itemsets_url': itemsets_url,
                'success': not error,
                'error': error,
                'warnings': warnings,
                'result': True,
            })
    else:
        form = UploadFileForm()  # An unbound form

    return render(request, 'upload.html', context={
        'form': form,
    })


@xframe_options_exempt
def serve_file(request, path):
    fo = codecs.open(os.path.join(DJANGO_TMP_HOME, path), mode='r', encoding='utf-8')
    data = fo.read()
    fo.close()
    response = HttpResponse(content_type='application/xml')
    response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(os.path.normpath(path))
    response.write(data)
    return response
