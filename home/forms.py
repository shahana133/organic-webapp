from django import forms
from .models import Product, UserProfile,Address


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'details', 'image', 'ctgry']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'image']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['full_name', 'phone', 'address_line', 'city', 'state', 'pincode']
        widgets = {
            'address_line': forms.Textarea(attrs={'rows': 2}),
        }