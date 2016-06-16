from django import forms
from config import configuration as config
import os


class SolrQuery(forms.Form):
    package_id = forms.CharField(max_length=300, label='Package ID', initial='*')
    content_type = forms.CharField(max_length=200, label='Content type', initial='*')
    additional_and = forms.CharField(max_length=500, label='AND')
    additional_and_not = forms.CharField(max_length=500, label='AND NOT')


class ArchivePath(forms.Form):
    tar_path = forms.CharField(max_length=300, label='Path for tar file', initial='', required=True)


class NERSelect(forms.Form):
    MODELS = (
        ('None', 'None'),
    )
    for model in os.listdir(config.stanford_ner_models):
        if model.endswith('.ser.gz'):
            MODELS += ((model, model),)
    ner_model = forms.ChoiceField(choices=MODELS, widget=forms.RadioSelect, label='Named Entity Recognition', initial='None')


class CSelect(forms.Form):
    MODELS = (
        ('None', 'None'),
    )
    for model in os.listdir(config.text_category_models):
        if model.endswith('.pkl'):
            MODELS += ((model, model),)
    category_model = forms.ChoiceField(choices=MODELS, widget=forms.RadioSelect, label='Text Classification', initial='None')
