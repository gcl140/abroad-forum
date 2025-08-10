from django.forms import ModelForm
from .models import *
from django.core.validators import FileExtensionValidator
from django import forms

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'image','image2', 'video', 'docs', 'link', 'tag']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full bg-gray-800 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-maroon placeholder-gray-500',
                'placeholder': 'Post title...'
            }),
            'content': forms.Textarea(attrs={
                'class': 'w-full bg-gray-800 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-maroon placeholder-gray-500',
                'rows': 3,
                'placeholder': "What's on your mind?"
            }),
            'link': forms.URLInput(attrs={
                'class': 'w-full bg-gray-800 rounded-lg px-4 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-maroon placeholder-gray-500',
                'placeholder': 'Attach a link (optional)'
            }),
            'tag': forms.Select(attrs={
                'class': 'w-full bg-gray-800 text-white px-4 py-2 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-maroon',
            }),
        }
    
    image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*'
        }),
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif'])]
    )
    
    video = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'video/*'
        }),
        validators=[FileExtensionValidator(allowed_extensions=['mp4', 'mov', 'avi', 'mkv'])]
    )
    
    docs = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': '.pdf,.doc,.docx,.ppt,.pptx'
        }),
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'ppt', 'pptx'])]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tag'].choices = [('', 'Select a tag')] + list(TAG_CHOICES)
        
    def clean(self):
        cleaned_data = super().clean()
        # Add any custom validation here
        return cleaned_data