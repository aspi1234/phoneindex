from django import forms
from django.utils import timezone
# Corrected import:
# We no longer have 'validate_imei' in models.py.
# Instead, we import 'validate_imei_format' and 'validate_imei_luhn'.
from .models import RegisteredDevice, TheftReport, validate_imei_format, validate_imei_luhn

class DeviceRegistrationForm(forms.ModelForm):
    # This field definition is now slightly redundant as the ModelForm
    # automatically pulls validators from the model. However, it's not causing the error.
    # To keep it cleaner as discussed, you could remove the 'validators' argument here.
    imei = forms.CharField(
        label='IMEI Number',
        max_length=15,
        # Remove this line if you want the ModelForm to inherit validators from the model
        # validators=[validate_imei], # <--- This was the old validator, now removed from models.py
        help_text='Enter the 15-digit IMEI number of your device. Dial *#06# to find it.',
        widget=forms.TextInput(attrs={'placeholder': '123456789012345'})
    )

    class Meta:
        model = RegisteredDevice
        fields = [
            'imei',
            'make',
            'model_name',
            'color',
            'storage_capacity',
            'distinguishing_features'
        ]
        widgets = {
            'make': forms.TextInput(attrs={'placeholder': 'e.g., Samsung, Apple, Google'}),
            'model_name': forms.TextInput(attrs={'placeholder': 'e.g., Galaxy S23, iPhone 15 Pro'}),
            'color': forms.TextInput(attrs={'placeholder': 'e.g., Black, Midnight Blue'}),
            'storage_capacity': forms.TextInput(attrs={'placeholder': 'e.g., 128GB, 256GB, 1TB'}),
            'distinguishing_features': forms.Textarea(attrs={'rows': 3, 'placeholder': 'e.g., Carbon fiber case, small scratch on bottom right corner'}),
        }
        labels = {
            'make': 'Make/Brand',
            'model_name': 'Model Name',
            'distinguishing_features': 'Distinguishing Features (Optional)',
        }
        # help_texts = { # Can remove if model's help_texts are sufficient
        # }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            if 'form-control' not in current_class:
                field.widget.attrs['class'] = f'{current_class} form-control'.strip()
            if isinstance(field.widget, forms.Textarea) and 'rows' not in field.widget.attrs:
                field.widget.attrs['rows'] = 3

# --- Theft Report Form (no changes needed) ---
class TheftReportForm(forms.ModelForm):
    date_time_of_theft = forms.DateTimeField(
        label='Date and Approximate Time of Theft',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        help_text='Please provide the date and time as accurately as possible.'
    )
    
    class Meta:
        model = TheftReport
        fields = [
            'region_of_theft',
            'date_time_of_theft',
            'is_time_approximate',
            'last_known_location',
            'circumstances',
            'additional_details',
        ]
        widgets = {
            'region_of_theft': forms.Select(attrs={'class': 'form-select'}),
            'last_known_location': forms.TextInput(attrs={'placeholder': 'e.g., Bambili Near Corners'}),
            'circumstances': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Describe how the theft occurred (e.g., left briefly unattended on table while some ACHU).'}),
            'additional_details': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any other details that might help (e.g., specific nearby landmarks, what else was taken).'}),
        }
        labels = {
            'region_of_theft': 'Region Where Theft Occurred',
            'is_time_approximate': 'The time provided is approximate',
            'last_known_location': 'Last Known Location of Device',
            'additional_details': 'Additional Details (Optional)',
        }
        help_texts = {
            'region_of_theft': 'Please select the region where the device was stolen.',
            'is_time_approximate': 'Check this box if the time of theft is an estimate.',
            'last_known_location': 'The address or general area where the device was last seen before it was stolen.',
            'circumstances': 'Provide a brief description of the events leading to the theft.',
        }
    
    def clean_date_time_of_theft(self):
        date_time_of_theft = self.cleaned_data.get('date_time_of_theft')
        if date_time_of_theft:
            if date_time_of_theft > timezone.now():
                raise forms.ValidationError("The date and time of theft cannot be in the future.")
        return date_time_of_theft

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            if 'form-control' not in current_class and not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = f'{current_class} form-control'.strip()
            elif isinstance(field.widget, forms.CheckboxInput) and 'form-check-input' not in current_class:
                 field.widget.attrs['class'] = f'{current_class} form-check-input'.strip()
            if isinstance(field.widget, forms.Textarea) and 'rows' not in field.widget.attrs:
                field.widget.attrs.setdefault('rows', 3)

# --- IMEI Verification Form (no changes needed, it's correct) ---
class IMEIVerificationForm(forms.Form):
    imei = forms.CharField(
        label="IMEI Number",
        max_length=15,
        min_length=15,
        validators=[validate_imei_format, validate_imei_luhn],
        widget=forms.TextInput(attrs={
            'placeholder': 'Enter 15-digit IMEI',
            'class': 'form-control form-control-lg text-center',
            'pattern': '\\d{15}',
            'title': 'IMEI must be exactly 15 digits',
            'inputmode': 'numeric'
        }),
        help_text='Dial *#06# to find your device\'s IMEI.'
    )
    def clean_imei(self):
        imei_data = self.cleaned_data.get('imei')
        if imei_data:
            return imei_data.strip()
        return imei_data