from django import forms


class SolrQuery(forms.Form):
    package_id = forms.CharField(max_length=300, label='Package ID')
    content_type = forms.CharField(max_length=200, label='Content type')


class NERSelect(forms.Form):
    MODELS = (
        ('None', 'None'),
        ('englishNERdefault', 'NER English'),
        ('englishNER7classes', 'NER English 7 classes'),
        ('gerNERdefault', 'NER German'),
        ('hunNERdefault', 'NER Hungarian'),
    )
    ner_model = forms.ChoiceField(choices=MODELS, widget=forms.RadioSelect, label='Named Entity Recognition')


class CSelect(forms.Form):
    MODELS = (
        ('None', 'None'),
        ('gerNewspaper', 'German Newspaper')
    )
    category_model = forms.ChoiceField(choices=MODELS, widget=forms.RadioSelect, label='Text Classification')
