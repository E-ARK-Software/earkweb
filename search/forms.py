from django import forms

PREDEFINED_CONTENT_TYPES = (
                ("*", "*"),
                ("text/plain", "text/plain"),
                ("application/xml", "application/xml"),
                ("image/tiff", "image/tiff"),
                )

class SearchForm(forms.Form):
    keyword = forms.CharField(max_length=100, initial="*")
    content_type = forms.MultipleChoiceField(widget=forms.SelectMultiple,choices=PREDEFINED_CONTENT_TYPES,initial={'*':[1,2]})


