from django.db import models
from django.contrib.auth.models import User 
from django.forms import ModelChoiceField
from django.core.validators import MaxValueValidator, MinValueValidator
import numpy as np

class Observable(models.Model):
    name = models.CharField(max_length=30000)
    def __str__(self):
        return self.name

class CommonInfo(models.Model):
    name = models.CharField(max_length=30)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['creation_date']

class Template(CommonInfo):
    last_modified = models.DateTimeField(auto_now=True)
    N = models.IntegerField(verbose_name="Reservoir Size", validators=[MinValueValidator(1)])
    spectral_radius = models.FloatField(verbose_name="Spectral radius", validators=[MinValueValidator(0)])
    dim_input = models.IntegerField(verbose_name="Dimension of input", validators=[MinValueValidator(1)])
    dim_output = models.IntegerField(verbose_name="Dimension of output", validators=[MinValueValidator(1)])
    proba = models.FloatField(verbose_name="Probability of a connection", validators=[MaxValueValidator(1),MinValueValidator(0)])
    input_bias = models.BooleanField(verbose_name="Input bias", default=True)
    seed = models.IntegerField(verbose_name="Random Seed (-1 corresponds to random)", default=-1)
    lr = models.FloatField(verbose_name="Leaking rate", validators=[MaxValueValidator(1),MinValueValidator(0)])
    IS = models.FloatField(verbose_name="Input Scaling", validators=[MinValueValidator(np.nextafter(0,1))])
    

    def __str__(self):
        return self.name

class Corpus(CommonInfo):
    data_in = models.FileField(default="None", verbose_name="Input file (must be CSV or NPY)")
    data_out = models.FileField(default="None", verbose_name="Output file (must be CSV or NPY)")
    size = models.IntegerField()
    dim_out = models.IntegerField()
    dim_in = models.IntegerField() 
    path = models.CharField(default="None",max_length=300000)
    def __str__(self):
        return self.name


class Network(CommonInfo):
    template = models.ForeignKey(Template, on_delete=models.DO_NOTHING)
    last_accessed = models.DateTimeField(auto_now=True, auto_now_add=False)
    auto_saved = models.BooleanField(default=False)




