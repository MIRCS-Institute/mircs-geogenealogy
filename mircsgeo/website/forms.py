from django import forms


class Uploadfile(forms.Form):
    file_upload = forms.FileField(label='Choose File:')


class AddDatasetKey(forms.Form):
    def __init__(self, dataset_columns, *args, **kwargs):
        self.dataset_columns = dataset_columns
        super(AddDatasetKey, self).__init__(*args, **kwargs)
        self.fields['dataset_columns'].choices = self.dataset_columns

    dataset_columns = forms.MultipleChoiceField(
        label='Dataset Columns:',
        choices=[],
        widget=forms.SelectMultiple(attrs={'class': 'ui fluid dropdown'})
    )
