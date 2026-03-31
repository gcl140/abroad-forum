from django import forms
from .models import CustomUser

class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}),
        label="Confirm Password"
    )
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={'tabindex': '-1', 'autocomplete': 'off'}))

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match!")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.username = self.cleaned_data["email"]  # Set the username to email
        if commit:
            user.save()
        return user


# class CustomUserForm(forms.ModelForm):
#     telephone = forms.RegexField(regex=r'^\+?\d{9,15}$', error_messages={
#     'invalid': "Enter a valid international phone number."
#         })
#     class Meta:
#         model = CustomUser
#         fields = ['first_name', 'last_name', 'email', 'telephone',  'profile_picture', 'bio', 'school', 'instagram_username']
#         widgets = {
#             'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
#             'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
#             'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            
#         }



from django import forms
from .models import CustomUser
import re

class CustomUserForm(forms.ModelForm):
    telephone = forms.RegexField(
        regex=r'^\+?\d{9,15}$',
        error_messages={'invalid': "Enter a valid international phone number (e.g., +255123456789)."},
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': '+255123456789'
        })
    )
    
    instagram_username = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'input-field',
            'placeholder': 'username (without @)'
        })
    )
    
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'telephone', 'profile_picture', 'bio', 'school', 'instagram_username', 'gender', 'grad_year']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-field',
                'placeholder': 'Email'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'input-field h-32',
                'placeholder': 'Tell us about yourself...',
                'rows': 4
            }),
            'school': forms.TextInput(attrs={
                'class': 'input-field',
                'placeholder': 'Your school or institution'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'hidden',
                'id': 'profile-picture-input'
            }),
            'gender': forms.Select(),
            
            'grad_year': forms.NumberInput(attrs={
                'class': 'input-field',
                'placeholder': 'Graduation Year'
            })
        }

    def clean_instagram_username(self):
        username = self.cleaned_data.get('instagram_username')
        if username:
            # Remove @ if present and any URL parts
            username = re.sub(r'^(https?://)?(www\.)?instagram\.com/', '', username)
            username = username.replace('@', '').strip('/')
            # username = f"https://www.instagram.com/{username}/" if username else ''
            return username
        return None

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user