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

class SearchData(forms.Form):
    def __init__(self, columnName, *args, **kwargs):
        self.columnName = columnName
        super(SearchData, self).__init__(*args, **kwargs)
        self.fields['columnName'].choices = self.columnName

    columnName = forms.ChoiceField(
        label='Search this column:',
        choices=[],
        widget=forms.Select(attrs={'class': 'ui fluid search selection dropdown'})
    )
    queryString = forms.CharField(
        label='For this value:',
        widget=forms.TextInput(attrs={'class': 'ui input'})
    )