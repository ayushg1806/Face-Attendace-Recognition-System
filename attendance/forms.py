from django import forms
from django.contrib.auth.models import User
from .models import EmployeeProfile

class EmployeeSignUpForm(forms.Form):
    username = forms.CharField(max_length=150)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)
    email = forms.EmailField(required=False)
    password = forms.CharField(widget=forms.PasswordInput)
    employee_id = forms.CharField(max_length=50)
    department = forms.CharField(max_length=100, required=False)
    face_image_data = forms.CharField(widget=forms.HiddenInput, required=False)

class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
