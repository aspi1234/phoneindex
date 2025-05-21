from django import forms
from django.utils import timezone
from .models import RegisteredDevice, validate_imei,TheftReport # Import validate_imei if you want to re-apply it here or rely on model validation

class DeviceRegistrationForm(forms.ModelForm):
    # If you want to use the exact same IMEI validation as the model,
    # the model's validation will run upon form.save() or full_clean().
    # However, to get errors displayed next to the field during form validation,
    # you can explicitly add the validator to the form field too.
    # ModelForm usually picks up validators from model fields, but being explicit can be good.
    imei = forms.CharField(
        label='IMEI Number',
        max_length=15,
        validators=[validate_imei], # Using the same validator from models.py
        help_text='Enter the 15-digit IMEI number of your device. Dial *#06# to find it.',
        widget=forms.TextInput(attrs={'placeholder': '123456789012345'})
    )

    class Meta:
        model = RegisteredDevice
        # Fields that the user will fill out.
        # 'owner' will be set in the view.
        # 'status' will default to 'NORMAL' as per the model.
        # 'registration_date' and 'last_updated' are auto-set.
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
        help_texts = {
            # Model help_texts are usually sufficient, but can be overridden here if needed
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to all fields
        for field_name, field in self.fields.items():
            # Add form-control class
            current_class = field.widget.attrs.get('class', '')
            if 'form-control' not in current_class:
                field.widget.attrs['class'] = f'{current_class} form-control'.strip()
            
            # For Textarea, ensure form-control doesn't conflict with rows if you use CSS to set height
            if isinstance(field.widget, forms.Textarea) and 'rows' not in field.widget.attrs:
                field.widget.attrs['rows'] = 3 # Default rows if not set in Meta.widgets

# --- NEW THEFT REPORT FORM ---
class TheftReportForm(forms.ModelForm):
    # Use a more user-friendly widget for date and time input if desired
    date_time_of_theft = forms.DateTimeField(
        label='Date and Approximate Time of Theft',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        help_text='Please provide the date and time as accurately as possible.'
    )
    # is_time_approximate is a BooleanField, will render as a checkbox by default.
    # We can customize its label or widget if needed.
    
    class Meta:
        model = TheftReport
        # Fields the user will fill out for the report.
        # 'device' will be set in the view.
        # 'case_id' will be auto-generated.
        # 'status' will default in the model.
        # 'reported_at' and 'last_updated' are auto-set.
        fields = [
            'region_of_theft', # Region field
            'date_time_of_theft',
            'is_time_approximate',
            'last_known_location',
            'circumstances',
            'additional_details',
        ]
        widgets = {
            'region_of_theft': forms.Select(attrs={'class': 'form-select'}), # Ensure Bootstrap styling
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
    
    # --- ADD THIS VALIDATION METHOD ---
    def clean_date_time_of_theft(self):
        # Get the date and time from the form's cleaned data
        date_time_of_theft = self.cleaned_data.get('date_time_of_theft')

        # Check if a date was provided (it should be, as the field is required by default)
        if date_time_of_theft:
            # Compare with the current time (timezone-aware)
            # timezone.now() returns a timezone-aware datetime object
            if date_time_of_theft > timezone.now():
                raise forms.ValidationError("The date and time of theft cannot be in the future.")
        
        # Always return the cleaned data, whether it's changed or not
        return date_time_of_theft

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Apply Bootstrap styling to all fields
        for field_name, field in self.fields.items():
            current_class = field.widget.attrs.get('class', '')
            if 'form-control' not in current_class and not isinstance(field.widget, forms.CheckboxInput):
                # CheckboxInput doesn't typically use form-control, but form-check-input
                field.widget.attrs['class'] = f'{current_class} form-control'.strip()
            elif isinstance(field.widget, forms.CheckboxInput) and 'form-check-input' not in current_class:
                 field.widget.attrs['class'] = f'{current_class} form-check-input'.strip()

            if isinstance(field.widget, forms.Textarea) and 'rows' not in field.widget.attrs:
                # Default rows if not set in Meta.widgets (though we set it for circumstances & additional_details)
                field.widget.attrs.setdefault('rows', 3)