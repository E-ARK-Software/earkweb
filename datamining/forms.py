from django import forms


class SolrQuery(forms.Form):
    package_id = forms.CharField(max_length=300, label='Package ID', initial='*')
    content_type = forms.CharField(max_length=200, label='Content type', initial='*')
    additional_query = forms.CharField(max_length=500, label='Additional', initial='*')


class ArchivePath(forms.Form):
    tar_path = forms.CharField(max_length=300, label='Path for tar file', initial='/home/janrn/test.tar')


class NERSelect(forms.Form):
    MODELS = (
        ('None', 'None'),
        ('englishNERdefault', 'NER English'),
        ('englishNER7classes', 'NER English 7 classes'),
        ('gerNERdefault', 'NER German'),
        ('hunNERdefault', 'NER Hungarian'),
    )
    ner_model = forms.ChoiceField(choices=MODELS, widget=forms.RadioSelect, label='Named Entity Recognition', initial='None')


class CSelect(forms.Form):
    MODELS = (
        ('None', 'None'),
        ('gerNewspaper', 'German Newspaper')
    )
    category_model = forms.ChoiceField(choices=MODELS, widget=forms.RadioSelect, label='Text Classification', initial='None')
