import re
from urllib.parse import urlparse

from django import forms
from django.forms import CharField, FileField, Form, MultipleChoiceField, SelectMultiple, TextInput
from django.utils.translation import gettext as _

import logging

from taggit.forms import TagField

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

    # Field is hidden!
    package_name = forms.CharField(widget=forms.HiddenInput())
    # Field is hidden!
    external_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    title = forms.CharField(label=_('Information package title'), max_length=100,  widget=forms.TextInput(attrs ={'placeholder': _('Data set title')}))
    description = forms.CharField(label=_('Information package description'), max_length=50000, widget=forms.Textarea(attrs ={'placeholder': _('Data set description')}))
    original_creation_date = forms.CharField(label=_('Original creation date'), max_length=100, widget=forms.TextInput(
        attrs={'placeholder': _('dd.mm.yyyy'),
               'onclick': "$('#id_original_creation_date').datepicker({dateFormat:'dd.mm.yy',changeYear: true, yearRange: '-200:+00'});$('#id_creation_date').datepicker('show');"}),
                                       required=False)
    tags = forms.CharField(max_length=100, widget=forms.TextInput(attrs={
        'placeholder': _('Please enter 2 characters to get tag suggestions or write a custom tag and press enter to add it'),
        'id': 'pp',
    }), required=False)
    hidden_user_tags = forms.CharField(max_length=10000, widget=forms.HiddenInput(attrs={
        'id': 'pp_tags_hidden',
    }), required=False)

    #Validation of the input
    def clean_package_name(self):
        package_name = self.cleaned_data['package_name']
        if package_name == _('PleaseAddNameOfPackage'):
            raise forms.ValidationError(_('ModifyInitialValue'))
        if re.findall(r"[^A-Za-z0-9.\-_]+", package_name):
            raise forms.ValidationError(_('Only alphanumeric characters plus hyphen (\'-\'), underscore (\'_\'), and dot  (\'.\') are allowed.'))
        return package_name

    def clean_external_id(self):
        external_id = self.cleaned_data['external_id']
        try:
            urlparse(external_id)
        except Exception as e:
            raise forms.ValidationError(e)
        return external_id

    def clean_title(self):
        title = self.cleaned_data['title']
        if title == _('PleaseAddTitleOfPackage'):
            raise forms.ValidationError(_('ModifyInitialValue'))
        return title
    def clean_change(self):
        description = self.form
        if not description.has_changed():
            raise forms.ValidationError(_('ModifyInitialValue'))
        return description


class MetaFormStep2(forms.Form):
    pass
    #locations = forms.CharField(label=_('Location metadata'), max_length=4096, widget=forms.Textarea(attrs={'rows': '2'}))


class MetaFormStep3(forms.Form):

    contact_point = forms.CharField(label=_('Contact'), max_length=255,
                                    widget=forms.TextInput(attrs ={'placeholder': _('Contact')}))
    contact_email = forms.EmailField(label=_('Contact email'),
                                     widget=forms.EmailInput({'placeholder': 'contact@email.com'}))
    publisher = forms.CharField(label=_('Maintainer'), max_length=255,
                                widget=forms.TextInput(attrs ={'placeholder': _('Maintainer')}))
    publisher_email = forms.EmailField(label=_('MaintainerEmail'),
                                       widget=forms.EmailInput({'placeholder': 'maintainer@email.com'}))
    language = forms.CharField(label=_('MainLanguageOfPackage'), max_length=255,
                               widget=forms.TextInput(attrs ={'id': 'PP_lang'}), initial=(_('MainInitialLanguage')))


class MetaFormStep4(forms.Form):
    pass


class MetaFormStep5(forms.Form):

    distribution_label = forms.CharField(label=_('Representation label'), max_length=50, widget=forms.TextInput(
        attrs={'placeholder': _('Representation label')}))

    access_rights = forms.ChoiceField(label=_('AccessRightsField'),
      choices = [
            ("Restricted", _('RestrictedAccess')),
            ("CC BY", _('CreativeCommonsAttribution')),
            ("CC BY-SA", _('CreativeCommonsAttributionShareAlike')),
            ("CC BY-ND", _('CreativeCommonsAttributionNoDerivatives')),
            ("CC BY-NC", _('CreativeCommonsAttributionNonCommercial')),
            ("CC BY-NC-SA", _('CreativeCommonsAttributionNonCommercialShareAlike')),
            ("CC BY-NC-ND", _('CreativeCommonsAttributionNonCommercialNoDerivatives')),
            ("CC0", _('CreativeCommonsZero')),
            ("GPL-3.0", _('GNUGeneralPublicLicensev3.0')),
            ("MIT", _('MITLicense')),
            ("Apache-2.0", _('ApacheLicense2.0')),
            ("BSD-3-Clause", _('BSD3ClauseLicense'))
        ],
    )

    distribution_description = forms.CharField(label=_('Representation description'), max_length=4096, widget=forms.Textarea(attrs={'rows': '2'}))

    def __init__(self, *args, **kwargs):
        super(MetaFormStep5, self).__init__(*args, **kwargs)
