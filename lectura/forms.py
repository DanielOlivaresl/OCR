from django import forms

class DocumentForm(forms.Form):
    file = forms.FileField(label="Selecciona un archivo", required=True)
