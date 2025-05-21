from django.contrib import admin
from .models import RegisteredDevice,TheftReport

from django.contrib import admin
from .models import RegisteredDevice, TheftReport # Import TheftReport

# Inline Admin for TheftReport to show on RegisteredDevice page
class TheftReportInline(admin.StackedInline): # Or admin.TabularInline for a more compact view
    model = TheftReport
    can_delete = False # Usually, you wouldn't delete a report directly, but resolve it
    verbose_name_plural = 'Theft Report Details'
    # Fields to display/edit in the inline form
    fields = ('case_id', 'region_of_theft', 'date_time_of_theft', 'is_time_approximate', 'last_known_location', 'circumstances', 'additional_details', 'status', 'reported_at', 'last_updated')
    readonly_fields = ('case_id', 'reported_at', 'last_updated') # Case ID and timestamps are auto-set/managed
    extra = 0 # Don't show extra blank forms for adding a new report via inline by default
    # You might want to hide this inline if the device status is not 'STOLEN'
    # This requires more complex logic, possibly by overriding get_inline_instances or get_formsets_with_inlines

@admin.register(TheftReport)
class TheftReportAdmin(admin.ModelAdmin):
    list_display = (
        'case_id',
        'region_of_theft',
        'device_info', # Custom method to display device make/model/IMEI
        'date_time_of_theft', 
        'status',
        'reported_at'
    )
    list_filter = ('status', 'region_of_theft','date_time_of_theft', 'reported_at')
    search_fields = ('case_id', 'device__imei', 'device__make', 'device__model_name', 'last_known_location')
    readonly_fields = ('case_id', 'reported_at', 'last_updated') # Case ID is auto-generated

    # Fields to display in the form for adding/editing a TheftReport directly
    # Note: 'device' field will be a dropdown to select a RegisteredDevice.
    # This direct creation path for TheftReport might be less common than via the device reporting flow.
    fieldsets = (
        (None, {
            'fields': ('device', 'case_id', 'status','region_of_theft') 
        }),
        ('Theft Details', {
            'fields': ('date_time_of_theft', 'is_time_approximate', 'last_known_location', 'circumstances', 'additional_details')
        }),
        ('Timestamps', {
            'fields': ('reported_at', 'last_updated'),
            'classes': ('collapse',)
        }),
    )
    
    # Custom method to display device info in list_display
    def device_info(self, obj):
        if obj.device:
            return f"{obj.device.make} {obj.device.model_name} ({obj.device.imei})"
        return "N/A"
    device_info.short_description = 'Associated Device'
    # autocomplete_fields = ['device'] # If you have many devices

@admin.register(RegisteredDevice)
class RegisteredDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'imei', 
        'make', 
        'model_name', 
        'owner_email', # Custom method to display owner's email
        'status', 
        'registration_date',
        'last_updated'
    )
    list_filter = ('status', 'make', 'registration_date', 'owner') # Filter by owner directly
    search_fields = ('imei', 'make', 'model_name', 'owner__email', 'owner__first_name', 'owner__last_name') # Search by owner's details
    readonly_fields = ('registration_date', 'last_updated') # These fields are auto-set

    fieldsets = (
        (None, {
            'fields': ('owner', 'imei', 'status')
        }),
        ('Device Details', {
            'fields': ('make', 'model_name', 'color', 'storage_capacity', 'distinguishing_features')
        }),
        ('Timestamps', {
            'fields': ('registration_date', 'last_updated'),
            'classes': ('collapse',) # Makes this section collapsible
        }),
    )

    # Optional: For better display of the owner in list_display
    def owner_email(self, obj):
        if obj.owner:
            return obj.owner.email
        return None
    owner_email.short_description = 'Owner Email' # Column header
    owner_email.admin_order_field = 'owner__email' # Allows sorting by owner's email

    # To make the owner field a searchable dropdown in the admin form if you have many users
    # autocomplete_fields = ['owner'] # Requires owner model to have search_fields defined in its admin

    # If you want to add a device directly in admin, owner field will be a dropdown.
    # Ensure your CustomUserAdmin has search_fields = ['email', 'first_name', 'last_name']
    # for autocomplete_fields to work well.