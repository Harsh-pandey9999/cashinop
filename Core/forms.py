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
        fields = ['title', 'slug', 'content', 'featured_image', 'published', 'is_featured', 
                'meta_description', 'meta_keywords']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10, 'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'meta_description': forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}),
            'meta_keywords': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'slug': 'A URL-friendly version of the title. Will be automatically generated if left blank.',
            'meta_description': 'Brief description for search engines (max 160 characters).',
            'meta_keywords': 'Comma-separated keywords for SEO (optional).',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False  # Make slug optional as it's auto-generated
        
    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        if not slug:
            # Auto-generate slug from title if not provided
            slug = slugify(self.cleaned_data.get('title', ''))
        return slug