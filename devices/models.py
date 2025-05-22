from django.db import models,IntegrityError
from django.conf import settings # To refer to the CustomUser model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re # For basic IMEI validation
from django.utils import timezone # For date operations

# Basic IMEI validator (length and digits only - Luhn algorithm is more complex)
def validate_imei(value):
    if not re.match(r'^\d{15}$', value): # Checks if it's exactly 15 digits
        raise ValidationError(
            _('%(value)s is not a valid IMEI. It must be 15 digits.'),
            params={'value': value},
        )
    # A more advanced validation might include the Luhn algorithm check here.

def validate_imei_luhn(value):
    """
    Validates the IMEI using the Luhn algorithm (Mod 10 check).
    Assumes the value is already 15 digits, as checked by validate_imei_format.
    """
    # Convert string to list of integers
    digits = [int(d) for d in value]

    # Drop the last digit (checksum digit)
    checksum_digit = digits.pop()
    
    # Reverse the remaining digits
    reversed_digits = digits[::-1]

    total = 0
    for index, digit in enumerate(reversed_digits):
        if index % 2 == 0: # Double every second digit
            doubled_digit = digit * 2
            if doubled_digit > 9: # If doubled digit is 10 or more, sum its digits
                total += (doubled_digit % 10) + (doubled_digit // 10)
            else:
                total += doubled_digit
        else: # Add other digits as they are
            total += digit

    # Compare the calculated checksum with the actual checksum digit
    if (total + checksum_digit) % 10 != 0:
        raise ValidationError(
            _('The IMEI checksum is invalid. Please check your IMEI.'),
        )

class RegisteredDevice(models.Model):
    STATUS_NORMAL = 'NORMAL'
    STATUS_STOLEN = 'STOLEN'
    STATUS_RECOVERED = 'RECOVERED' # Or 'RESOLVED' as per user story for case resolution
    STATUS_FALSE_ALARM = 'FALSE_ALARM' # Added from user story context

    STATUS_CHOICES = [
        (STATUS_NORMAL, _('Normal')),
        (STATUS_STOLEN, _('Reported Stolen')),
        (STATUS_RECOVERED, _('Recovered/Resolved')),
        (STATUS_FALSE_ALARM, _('False Alarm')),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, # Refers to your CustomUser model
        on_delete=models.CASCADE, # If user is deleted, their devices are also deleted
        related_name='registered_devices' # Allows access like user.registered_devices.all()
    )
    imei = models.CharField(
        _('IMEI Number'),
        max_length=15,
        unique=True, # IMEI must be unique across all devices
        validators=[validate_imei],
        help_text=_('Enter the 15-digit IMEI number of your device. Dial *#06# to find it.')
    )
    make = models.CharField(_('Make/Brand'), max_length=100, help_text=_('e.g., Samsung, Apple, Google'))
    model_name = models.CharField(_('Model Name'), max_length=100, help_text=_('e.g., Galaxy S23, iPhone 15 Pro'))
    color = models.CharField(_('Color'), max_length=50)
    storage_capacity = models.CharField(
        _('Storage Capacity'), 
        max_length=20, 
        help_text=_('e.g., 128GB, 256GB, 1TB')
    )
    distinguishing_features = models.TextField(
        _('Distinguishing Features'), 
        blank=True, 
        null=True, # Allow it to be empty in the database
        help_text=_('e.g., Carbon fiber case, small scratch on bottom right corner')
    )
    registration_date = models.DateTimeField(_('Registration Date'), auto_now_add=True)
    last_updated = models.DateTimeField(_('Last Updated'), auto_now=True) # To track when status or details change
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NORMAL
    )

    def __str__(self):
        return f"{self.make} {self.model_name} (IMEI: {self.imei}) - Owner: {self.owner.email}"

    class Meta:
        verbose_name = _('Registered Device')
        verbose_name_plural = _('Registered Devices')
        ordering = ['-registration_date'] # Default ordering for queries

# --- NEW THEFT REPORT MODEL ---
class TheftReport(models.Model):
    REPORT_STATUS_ACTIVE = 'ACTIVE'
    REPORT_STATUS_OWNER_RECOVERY = 'OWNER_RECOVERED' # Device recovered by owner directly
    REPORT_STATUS_FINDER_RETURN = 'FINDER_RETURNED' # Device returned via finder process
    REPORT_STATUS_FALSE_ALARM = 'RESOLVED_FALSE_ALARM' # Report was a false alarm

    REPORT_STATUS_CHOICES = [
        (REPORT_STATUS_ACTIVE, _('Active Report')),
        (REPORT_STATUS_OWNER_RECOVERY, _('Resolved - Recovered by Owner')),
        (REPORT_STATUS_FINDER_RETURN, _('Resolved - Returned by Finder')),
        (REPORT_STATUS_FALSE_ALARM, _('Resolved - False Alarm')),
    ]

    # Link to the device that was stolen.
    # OneToOneField ensures a device can only have one *active* theft report.
    # If a device is stolen multiple times, you might need a ForeignKey and an 'is_active_report' flag,
    # or a different way to handle historical reports. For now, OneToOne for simplicity.
    # --- UPDATED REGION_CHOICES ---
    REGION_CHOICES = [
        ('AD', _('Adamaoua')),
        ('CE', _('Center')),        # Corrected from your 'Center' to 'Centre' for common French spelling, adjust if 'Center' is preferred.
        ('ES', _('East')),          # Est in French
        ('FN', _('Far North')),     # Extrême-Nord in French
        ('LT', _('Littoral')),
        ('NO', _('North')),         # Nord in French
        ('NW', _('North-West')),    # Nord-Ouest in French
        ('OU', _('West')),          # Ouest in French (OU is a good short code)
        ('SU', _('South')),         # Sud in French
        ('SW', _('South-West')),    # Sud-Ouest in French
        ('UN', _('Unknown/Other')), # Kept the 'Unknown' option, can be removed if not needed
    ]
    # --- END OF UPDATED REGION_CHOICES ---

    device = models.OneToOneField(
        RegisteredDevice,
        on_delete=models.CASCADE,
        related_name='theft_report'
    )
    # Add the new region_of_theft field
    region_of_theft = models.CharField(
        _('Region of Theft'),
        max_length=2, # Max length of your region codes (e.g., 'UNK', 'AD', 'NW')
        choices=REGION_CHOICES,
        # Decide if this field is mandatory. If so, remove blank=True, null=True.
        # For Case ID generation, it will be treated as required.
        # blank=False, null=False, # Making it required by default
        help_text=_('Select the region where the theft occurred.')
    )
    case_id = models.CharField(
        _('Case ID'),
        max_length=30, # e.g., CR-20231027-YDE-0001 (CR-YYYYMMDD-XXX-SSSS) -> 2 + 1 + 8 + 1 + 3 + 1 + 4 = 20. Let's use 25 for safety.
        unique=True,
        editable=False
    )
    date_time_of_theft = models.DateTimeField(_('Date and Time of Theft'))
    is_time_approximate = models.BooleanField(_('Is Time Approximate?'), default=True)
    last_known_location = models.CharField(_('Last Known Location'), max_length=255)
    circumstances = models.TextField(_('Circumstances of Theft'))
    additional_details = models.TextField(_('Additional Details'), blank=True, null=True)
    
    reported_at = models.DateTimeField(_('Reported At'), auto_now_add=True)
    last_updated = models.DateTimeField(_('Report Last Updated'), auto_now=True)

    status = models.CharField(
        _('Report Status'),
        max_length=30,
        choices=REPORT_STATUS_CHOICES, # Make sure REPORT_STATUS_CHOICES is defined
        default='ACTIVE' # Assuming REPORT_STATUS_ACTIVE is defined
    )

    def __str__(self):
        return f"Theft Report {self.case_id} for {self.device.imei}"

    def _generate_case_id(self):
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')
        
        # Ensure region_of_theft is set. This should be guaranteed if the form requires it.
        if not self.region_of_theft:
            # This case should ideally not happen if the form enforces region selection.
            # Handle it gracefully, perhaps by defaulting to 'UNK' or raising an error earlier.
            # For now, let's assume it will be set. If it can be optional, the logic needs adjustment.
            raise ValueError("Region of theft must be set to generate a Case ID.")

        region_code = self.region_of_theft.upper() # Ensure region code is uppercase for consistency

        # Find the latest report for today AND this region to determine the next sequence number
        last_report_today_region = TheftReport.objects.filter(
            case_id__startswith=f'CR-{date_str}-{region_code}-'
        ).order_by('case_id').last()

        next_sequence = 1
        if last_report_today_region:
            try:
                last_sequence_str = last_report_today_region.case_id.split('-')[-1]
                next_sequence = int(last_sequence_str) + 1
            except (IndexError, ValueError):
                # Fallback: count reports for the day and region
                # This is less ideal as it doesn't guarantee a strict sequence if an ID was deleted or skipped
                next_sequence = TheftReport.objects.filter(
                    reported_at__date=today, 
                    region_of_theft=self.region_of_theft
                ).count() + 1
        
        if next_sequence > 9999:
            # Consider a more robust error or logging
            raise ValidationError("Case ID sequence limit reached for today in this region.")

        sequence_str = f"{next_sequence:04d}"
        return f"CR-{date_str}-{region_code}-{sequence_str}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.case_id: 
            # The form should have populated region_of_theft by now
            if not self.region_of_theft:
                # This state should be prevented by form validation making region_of_theft required
                raise IntegrityError("Cannot save TheftReport: region_of_theft is required to generate a Case ID.")

            while True:
                potential_case_id = self._generate_case_id()
                if not TheftReport.objects.filter(case_id=potential_case_id).exists():
                    self.case_id = potential_case_id
                    break
                # If collision, _generate_case_id will try next sequence in its next call within the loop
                # (This implies _generate_case_id's logic for finding next_sequence needs to be robust to repeated calls
                # or the loop needs to increment something itself if _generate_case_id is deterministic given the same state)
                # The current _generate_case_id relies on what's in DB, so re-querying is fine.
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Theft Report')
        verbose_name_plural = _('Theft Reports')
        ordering = ['-reported_at']

# Ensure RegisteredDevice model is defined above or imported if in separate file
# Ensure REPORT_STATUS_CHOICES, REPORT_STATUS_ACTIVE are defined within TheftReport or globally.

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import re

# ... (validate_imei, RegisteredDevice, TheftReport models as previously defined) ...


# --- NEW FOUND REPORT MODEL ---
class FoundReport(models.Model):
    CONDITION_CHOICES = [
        ('PERFECT', _('Perfect condition, like new')),
        ('GOOD', _('Good condition, minor wear')),
        ('FAIR', _('Fair condition, visible scratches/dents')),
        ('POOR', _('Poor condition, screen damaged or other issues')),
        ('NOT_WORKING', _('Not working / Unable to power on')),
        ('UNKNOWN', _('Condition unknown')),
    ]

    RETURN_METHOD_CHOICES = [
        ('POLICE', _('Deliver to a local police station')),
        ('ANONYMOUS_CHAT', _('Arrange anonymous handover (via this platform)')), # For future chat
        ('DIRECT_CONTACT', _('Willing to coordinate directly (share my contact info with owner)')),
        ('OTHER', _('Other (please specify in message)')),
    ]

    # This field links the found report to an existing theft report if a match is made.
    # It can be null initially, as the finder might not provide a perfect Case ID or IMEI,
    # and system matching might happen after submission or require admin intervention.
    theft_report = models.ForeignKey(
        TheftReport,
        on_delete=models.CASCADE, # If the original TheftReport is deleted, keep this FoundReport but unlink.
        null=True, blank=True,     # Can be unlinked initially or if no match.
        related_name='found_reports'
    )

    matched_device_direct = models.ForeignKey( # Renamed to avoid confusion if you already have 'matched_device'
        RegisteredDevice,
        on_delete=models.CASCADE, # CHANGE THIS: If RegisteredDevice is deleted, these FoundReports are also deleted.
        null=True, blank=True,
        related_name='direct_found_reports',
        help_text="Direct link to the registered device, if matched independently of a theft report."
    )

    # Information provided by the finder to help identify the device
    case_id_provided = models.CharField(
        _('Case ID (if known)'), 
        max_length=30, 
        blank=True, null=True,
        help_text=_("If you found a Case ID on the device's lock screen or were given one.")
    )
    imei_provided = models.CharField(
        _('IMEI (if known)'), 
        max_length=15, 
        blank=True, null=True, 
        validators=[validate_imei], # Can still validate if they provide it
        help_text=_("The 15-digit IMEI, if you can find it (*#06# or on device).")
    )
    device_description_provided = models.TextField(
        _('Device Description (if Case ID/IMEI unknown)'),
        blank=True, null=True,
        help_text=_("e.g., Black iPhone, Samsung with blue case, small crack on screen.")
    )

    # Details about the find
    date_found = models.DateTimeField(_('Date and Time Found'))
    location_found = models.TextField(_('Location Where Found'))
    device_condition = models.CharField(
        _('Condition of Device'),
        max_length=20,
        choices=CONDITION_CHOICES,
        default='UNKNOWN'
    )

    # Finder's preferences and optional information
    return_method_preference = models.CharField(
        _('Preferred Return Method'),
        max_length=20,
        choices=RETURN_METHOD_CHOICES
    )
    finder_message_to_owner = models.TextField(
        _('Message to Owner (Optional)'),
        blank=True, null=True
    )
    # Optional contact details for the finder
    # These should only be requested/used if return_method_preference is 'DIRECT_CONTACT' or 'OTHER'
    finder_name = models.CharField(_('Your Name (Optional)'), max_length=100, blank=True, null=True)
    finder_contact_email = models.EmailField(_('Your Email (Optional)'), blank=True, null=True)
    # For finder_contact_phone, consider using django-phonenumber-field or robust validation if you implement it
    finder_contact_phone = models.CharField(_('Your Phone Number (Optional)'), max_length=20, blank=True, null=True) 

    reported_at = models.DateTimeField(_('Found Report Submitted At'), auto_now_add=True)
    is_processed = models.BooleanField(_('Processed by System/Admin'), default=False, help_text="Indicates if this report has been reviewed or matched.")


    def __str__(self):
        if self.theft_report:
            return f"Found report linked to Case ID {self.theft_report.case_id} (submitted by finder)"
        elif self.case_id_provided:
            return f"Found report for Case ID '{self.case_id_provided}' (submitted by finder)"
        elif self.imei_provided:
            return f"Found report for IMEI '{self.imei_provided}' (submitted by finder)"
        return f"Found report submitted {self.reported_at.strftime('%Y-%m-%d')}"

    class Meta:
        verbose_name = _('Found Device Report')
        verbose_name_plural = _('Found Device Reports')
        ordering = ['-reported_at']