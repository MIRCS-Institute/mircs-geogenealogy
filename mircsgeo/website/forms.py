from django import forms


class UploadCsv(forms.Form):
    csv_file = forms.FileField(label='CSV File:')
