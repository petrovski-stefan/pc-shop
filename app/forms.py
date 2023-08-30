from django import forms

from .models import Product, Review


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        exclude = ['slug', 'sold', 'created_at', 'seller']

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for bound_field in self.visible_fields():
            bound_field.field.widget.attrs['class'] = 'form-control mb-2'


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        exclude = ['created_at', 'updated_at', 'product', 'customer']

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        for bound_field in self.visible_fields():
            bound_field.field.widget.attrs['class'] = 'form-control mb-2'
