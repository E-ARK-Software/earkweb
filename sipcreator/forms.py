from django.forms import CharField, FileField, Form, MultipleChoiceField, SelectMultiple, TextInput

PREDEFINED_CONTENT_TYPES = (
                ("*", "*"),
                ("text/plain", "text/plain"),
                ("application/xml", "application/xml"),
                ("image/tiff", "image/tiff"),
                )


def set_bootstrap_class(attrs=None):
    if not attrs:
        attrs = {}
    attrs['class'] = 'form-control'
    return attrs


class BootstrapTextInput(TextInput):
    def __init__(self, attrs=None):
        super(BootstrapTextInput, self).__init__(set_bootstrap_class(attrs))


class BootstrapSelectMultiple(SelectMultiple):
    def __init__(self, attrs=None):
        super(BootstrapSelectMultiple, self).__init__(set_bootstrap_class(attrs))


class SearchForm(Form):
    keyword = CharField(widget=BootstrapTextInput, max_length=100, initial="*")
    content_type = MultipleChoiceField(widget=BootstrapSelectMultiple, choices=PREDEFINED_CONTENT_TYPES,initial={'*': [1, 2]})


class UploadFileForm(Form):
    content_file = FileField(label='File')

class TinyUploadFileForm(Form):
    content_file = FileField(label='')
