from django import forms
from DataModel import models

class LoginForm(forms.Form):
    id = forms.CharField(max_length=7, min_length=7)
    password = forms.CharField(widget=forms.PasswordInput())


