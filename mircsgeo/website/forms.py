from django import forms


class Uploadfile(forms.Form):
    file_upload = forms.FileField(label='Choose File:')
