from django import forms
from django.utils import timezone
from .models import RegisteredDevice, validate_imei,TheftReport,FoundReport,validate_imei_luhn # Import validate_imei if you want to re-apply it here or rely on model validation

class DeviceRegistrationForm(forms.ModelForm):
    # If you want to use the exact same IMEI validation as the model,
    # the model's validation will run upon form.save() or full_clean().
    # However, to get errors displayed next to the field during form validation,
    # you can explicitly add the validator to the form field too.
    # ModelForm usually picks up validators from model fields, but being explicit can be good.
    imei = forms.CharField(
        label='IMEI Number',
        max_length=15,
        validators=[validate_imei,validate_imei_luhn], # Using the same validator from models.py
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

# --- NEW IMEI VERIFICATION FORM ---
class IMEIVerificationForm(forms.Form):
    imei = forms.CharField(
        label='IMEI Number',
        max_length=15,
        min_length=15, # Ensure it's exactly 15 characters on the form level too
        validators=[validate_imei,validate_imei_luhn], # Use our existing 15-digit validator
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg', # Larger input for prominence
            'placeholder': 'Enter 15-digit IMEI number'
        }),
        help_text='Dial *#06# on the phone to find its IMEI number.'
    )

    def clean_imei(self):
        # Additional cleaning if necessary, though validate_imei handles basic format.
        # For example, stripping whitespace just in case.
        imei_data = self.cleaned_data.get('imei')
        if imei_data:
            return imei_data.strip()
        return imei_data
    
class FoundDeviceForm(forms.ModelForm):
    date_found = forms.DateTimeField(
        label='Date and Approximate Time Found',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        help_text='Please provide the date and time as accurately as possible when you found the device.'
    )
    
    case_id_provided = forms.CharField(
        label='Case ID (if visible on device/known)',
        max_length=30,
        required=False, 
        help_text="Enter if you found a Case ID (e.g., CR-YYYYMMDD-REG-SSSS)."
    )
    imei_provided = forms.CharField(
        label='IMEI (if visible on device/known)',
        max_length=15,
        validators=[validate_imei],
        required=False,
        help_text="Enter the 15-digit IMEI if you can find it."
    )
    # device_description_provided will be handled by ModelForm default CharField -> TextInput
    # We will make it readonly in __init__ if pre-filled.

    class Meta:
        model = FoundReport
        fields = [
            'case_id_provided',
            'imei_provided',
            'device_description_provided',
            'date_found',
            'location_found',
            'device_condition',
            'return_method_preference',
            'finder_message_to_owner',
            'finder_name',
            'finder_contact_email',
            'finder_contact_phone',
        ]
        widgets = {
            # We will control device_description_provided's placeholder dynamically if not disabled
            'location_found': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Specific address or general area where the device was found.'}),
            'device_condition': forms.Select(), # Will use model choices
            'return_method_preference': forms.Select(), # Will use model choices
            'finder_message_to_owner': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Any message you would like to pass to the owner (optional).'}),
            'finder_name': forms.TextInput(attrs={'placeholder': 'Your Name (Optional)'}),
            'finder_contact_email': forms.EmailInput(attrs={'placeholder': 'Your Email (Optional - for owner to contact you)'}),
            'finder_contact_phone': forms.TextInput(attrs={'placeholder': 'Your Phone (Optional - for owner to contact you)'}),
            'device_description_provided': forms.Textarea(attrs={'rows': 2}), # Default widget
        }
        labels = {
            'device_description_provided': 'Device Description', # Keep it simple, help_text will guide
            'finder_contact_email': 'Your Contact Email (Optional)',
            'finder_contact_phone': 'Your Contact Phone (Optional)',
        }
        help_texts = {
            'device_description_provided': 'Pre-filled if Case ID/IMEI matched. Otherwise, please describe the device (e.g., Black iPhone, Samsung with blue case).',
            'finder_contact_email': 'Only provide if you chose "Willing to coordinate directly" and want the owner to email you.',
            'finder_contact_phone': 'Only provide if you chose "Willing to coordinate directly" and want the owner to call/text you.',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Pre-fill and make fields disabled if initial data is present
        # Using 'disabled' also means the browser won't submit the field's value,
        # so we'll rely on 'initial' data in the view or form's clean method for these.
        
        prefilled_identifier = False # Flag to track if Case ID or IMEI was pre-filled

        if self.initial.get('case_id_provided'):
            self.fields['case_id_provided'].widget.attrs['disabled'] = True
            self.fields['case_id_provided'].help_text = 'This Case ID was pre-filled.'
            self.fields['imei_provided'].required = False # Make IMEI optional if Case ID is given
            self.fields['imei_provided'].widget.attrs['placeholder'] = 'IMEI (Optional as Case ID provided)'
            prefilled_identifier = True

        if self.initial.get('imei_provided'):
            self.fields['imei_provided'].widget.attrs['disabled'] = True
            self.fields['imei_provided'].help_text = 'This IMEI was pre-filled.'
            self.fields['case_id_provided'].required = False # Make Case ID optional if IMEI is given
            self.fields['case_id_provided'].widget.attrs['placeholder'] = 'Case ID (Optional as IMEI provided)'
            prefilled_identifier = True
        
        # If an identifier (Case ID or IMEI) was pre-filled, also disable device_description_provided
        # because the pre-filled description from the view's get_initial is more accurate.
        if prefilled_identifier and self.initial.get('device_description_provided'):
            self.fields['device_description_provided'].widget.attrs['disabled'] = True
            self.fields['device_description_provided'].help_text = 'Device description pre-filled based on provided Case ID/IMEI.'
        elif not prefilled_identifier: # Only set placeholder if not pre-filled and disabled
             self.fields['device_description_provided'].widget.attrs['placeholder'] = 'e.g., Black iPhone with a red case, found near the park entrance.'


        # Apply Bootstrap styling to other fields
        for field_name, field in self.fields.items():
            current_attrs = field.widget.attrs
            # Ensure disabled fields also get 'form-control' for consistent appearance
            if current_attrs.get('disabled'):
                current_attrs['class'] = current_attrs.get('class', '') + ' form-control'
            elif isinstance(field.widget, forms.CheckboxInput):
                current_attrs['class'] = current_attrs.get('class', '') + ' form-check-input'
            elif isinstance(field.widget, forms.Select):
                current_attrs['class'] = current_attrs.get('class', '') + ' form-select'
            # DateTimeInput widget is already styled via its attrs in field definition
            elif not isinstance(field.widget, forms.DateTimeInput): 
                 current_attrs['class'] = current_attrs.get('class', '') + ' form-control'
            
            # Clean up extra spaces in class attribute
            if 'class' in current_attrs:
                current_attrs['class'] = ' '.join(current_attrs['class'].split())

            if isinstance(field.widget, forms.Textarea) and 'rows' not in current_attrs:
                current_attrs.setdefault('rows', 3)


    # --- VALIDATION FOR date_found ---
    def clean_date_found(self):
        date_value = self.cleaned_data.get('date_found')
        if date_value and date_value > timezone.now():
            raise forms.ValidationError("The date and time you found the device cannot be in the future.")
        return date_value

    def clean(self):
        cleaned_data = super().clean()
        return_method = cleaned_data.get('return_method_preference')
        contact_email = cleaned_data.get('finder_contact_email')
        contact_phone = cleaned_data.get('finder_contact_phone')

        if return_method == 'DIRECT_CONTACT' and not (contact_email or contact_phone):
            self.add_error(None, forms.ValidationError(
                "If you choose 'Willing to coordinate directly', please provide at least one method of contact (email or phone)."
            ))
        
        # Get identifier values, considering if they were disabled (and thus not in cleaned_data from POST)
        case_id = cleaned_data.get('case_id_provided')
        if self.initial.get('case_id_provided') and self.fields['case_id_provided'].widget.attrs.get('disabled'):
            case_id = self.initial.get('case_id_provided')

        imei = cleaned_data.get('imei_provided')
        if self.initial.get('imei_provided') and self.fields['imei_provided'].widget.attrs.get('disabled'):
            imei = self.initial.get('imei_provided')
            
        description = cleaned_data.get('device_description_provided')
        if self.initial.get('device_description_provided') and self.fields['device_description_provided'].widget.attrs.get('disabled'):
            description = self.initial.get('device_description_provided')

        if not (case_id or imei or description):
            self.add_error(None, forms.ValidationError(
                "Please provide at least one identifier for the device: Case ID, IMEI, or a Device Description."
            ))
        return cleaned_data