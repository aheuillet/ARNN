from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Network, Template, Corpus, Observable
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.conf import settings

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            'username',
            'first_name',
            'last_name',
            'email',
        )

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.fisrt_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']

        if commit:
            user.save()

        return user


class NetworkForm(forms.ModelForm):
    class Meta:
        model = Network
        fields = ('name', 'template',) 

    def __init__(self, user, *args, **kwargs):
            super(NetworkForm, self).__init__(*args, **kwargs)
            self.fields['template'].queryset = Template.objects.filter(owner=user)


    
class TemplateForm(forms.ModelForm):
    N = forms.IntegerField(required=True, max_value=settings.MAX_SIZE_RESERVOIR)
    dim_input = forms.IntegerField(required=True, max_value=settings.MAX_DIM_INPUT)
    dim_output = forms.IntegerField(required=True, max_value=settings.MAX_DIM_OUTPUT)
    class Meta:
        model = Template
        s = []
        for a in Template._meta.get_fields():
            b = str(a).replace("ARNN.Template.", "")
            if (b != '<ManyToOneRel: ARNN.network>') and (b != 'id') and (b != 'input_bias') and (b != 'owner') and (b != 'creation_date') and (b != 'last_modified'): 
                s.append(b)
        fields = s 

class CorpusForm(forms.ModelForm):
    class Meta:
        model = Corpus
        fields = ['name', 'data_in', 'data_out']

class CorpusGenerateForm(forms.Form):
    name = forms.CharField(max_length=30, required=True)
    size = forms.IntegerField(label="Length of the corpus",required=True)
    dim = forms.IntegerField(label="Number of columns", required=True)
    min_val = forms.IntegerField(label="Minimal value to be generated", required=True)
    max_val = forms.IntegerField(label="Maximal value to be generated", required=True)
    seed = forms.IntegerField(label="Seed for random generation", initial=-1)

class TaskForm(forms.Form):
    TYPE_CHOICES = (
        ('Train', 'Train'),
        ('Test', 'Test'),
    )
    kind_task = forms.ChoiceField(choices=TYPE_CHOICES, widget=forms.Select())
    corpus = forms.ModelChoiceField(label="Corpus matching dimensions", queryset=Corpus.objects.all())
    start = forms.IntegerField(required=True, min_value=0)
    stop = forms.IntegerField(required=True, min_value=1)

    def __init__(self, *args, **kwargs):
        requser = kwargs.pop('user', None)
        super(TaskForm, self).__init__(*args, **kwargs)
        corpus_user = get_object_or_404(User, username=settings.SHARED_CORPUS_ACCOUNT )
        self.fields['corpus'].queryset = Corpus.objects.filter(Q(owner=requser) | Q(owner=corpus_user))


class ObservableForm(forms.Form):
    observable = forms.ModelChoiceField(queryset=Observable.objects.all(), to_field_name="name")
    periodicity = forms.IntegerField(required=True, min_value=1)