from django import forms
from .models import GameCards,About,BlogPost

class PostForm(forms.ModelForm):
    class Meta:
        model = GameCards
        fields = ['title', 'image', 'description', 'redirect_link']

class AboutForm(forms.ModelForm):
    class Meta:
        model = About
        fields = ['title', 'content']

class BlogPostForm(forms.ModelForm):
    class Meta:
        model = BlogPost
        fields = ['title', 'content', 'featured_image', 'published']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }