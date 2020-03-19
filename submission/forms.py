from django import forms
from django.forms import CharField, FileField, Form, MultipleChoiceField, SelectMultiple, TextInput
from django.utils.translation import gettext as _

import logging
logger = logging.getLogger(__name__)


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


class MetaFormStep1(forms.Form):

    # Define the core
    title = forms.CharField(label=_('Information package title'), max_length=100,  widget=forms.TextInput(attrs ={'placeholder': _('Information package title')}))
    description = forms.CharField(label=_('Information package description'), max_length=50000, widget=forms.Textarea(attrs ={'placeholder': _('Information package description')}))

    #Validation of the input
    def clean_title(self):
        title = self.cleaned_data['title']
        if title == _('PleaseAddNameOfPackage'):
            raise forms.ValidationError(_('ModifyInitialValue'))
        return title
    def clean_change(self):
        description = self.form
        if not description.has_changed():
            raise forms.ValidationError(_('ModifyInitialValue'))
        return description


class MetaFormStep2(forms.Form):

    contact_point = forms.CharField(label=_('ContactOfPackage'), max_length=255,
                                    widget=forms.TextInput(attrs ={'placeholder': _('ContactOfPackage')}))
    contact_email = forms.EmailField(label=_('ContactEmailOfPackage'),
                                     widget=forms.EmailInput({'placeholder': 'contact@eark-project.com'}))
    publisher = forms.CharField(label=_('PublisherOfPackage'), max_length=255,
                                widget=forms.TextInput(attrs ={'placeholder': _('PublisherOfPackage')}))
    publisher_email = forms.EmailField(label=_('PublisherEmailOfPackage'),
                                       widget=forms.EmailInput({'placeholder': 'publisher@eark-project.com'}))
    language = forms.CharField(label=_('MainLanguageOfPackage'), max_length=255,
                               widget=forms.TextInput(attrs ={'id': 'PP_lang'}), initial=(_('MainInitialLanguage')))


class MetaFormStep4(forms.Form):

    distribution_label = forms.CharField(label=_('Representation label'), max_length=50, widget=forms.TextInput(
        attrs={'placeholder': _('Representation label')}))

    access_rights = forms.ChoiceField(label=_('AccessRightsField'),
      choices=[("free", _('DistributionAccessRightsValueFree')), ("limited", _('DistributionAccessRightsValueLimited'))],
    )

    distribution_description = forms.CharField(label=_('Representation description'), max_length=4096, widget=forms.Textarea(attrs={'rows': '2'}))


    def __init__(self, *args, **kwargs):
        super(MetaFormStep4, self).__init__(*args, **kwargs)
