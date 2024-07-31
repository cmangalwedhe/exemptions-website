from django import forms


class CSVUploadForm(forms.Form):
    file = forms.FileField(
        label='Upload CSV file',
        widget=forms.FileInput(attrs={'accept': 'csv', 'required': True})
    )