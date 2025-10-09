# apps/core/form_utils.py
from django import forms
from django.core.exceptions import ValidationError

class BootstrapFormMixin:
    """
    Mixin to add Bootstrap CSS classes to form fields
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field.widget, (forms.TextInput, forms.EmailInput,
                                         forms.NumberInput, forms.DateInput,
                                         forms.DateTimeInput, forms.TimeInput)):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.Textarea):
                field.widget.attrs['class'] = 'form-control'
            elif isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = 'form-check-input'
            elif isinstance(field.widget, forms.RadioSelect):
                field.widget.attrs['class'] = 'form-check-input'

def validate_positive(value):
    """Validate that value is positive"""
    if value <= 0:
        raise ValidationError('Value must be positive.')

def validate_symbol_format(value):
    """Validate stock symbol format"""
    if not value.isalnum():
        raise ValidationError('Symbol can only contain letters and numbers.')
    if len(value) > 20:
        raise ValidationError('Symbol cannot exceed 20 characters.')