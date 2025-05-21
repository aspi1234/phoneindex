from django.urls import path
from .views import RegisterDeviceView, UserDeviceListView, ReportDeviceStolenView,TheftReportDetailView # Import ReportDeviceStolenView

app_name = 'devices'  # Define an application namespace

urlpatterns = [
    path('register/', RegisterDeviceView.as_view(), name='register_device'),
    path('my-devices/', UserDeviceListView.as_view(), name='user_device_list'),
    # Add other device-related URLs here in the future (e.g., device detail, edit, report stolen)
     # --- NEW URL FOR REPORTING A DEVICE STOLEN ---
    # It expects an integer 'device_pk' in the URL, which corresponds to the RegisteredDevice's primary key.
    path('<int:device_pk>/report-stolen/', ReportDeviceStolenView.as_view(), name='report_device_stolen'),
    # Add other device-related URLs here in the future
    # e.g., path('<int:pk>/detail/', DeviceDetailView.as_view(), name='device_detail'),
    # e.g., path('<int:pk>/edit/', DeviceEditView.as_view(), name='device_edit'),
    # --- NEW URL FOR VIEWING THEFT REPORT DETAILS ---
    # It expects an integer 'pk' which is the primary key of the TheftReport instance.
    path('report/<int:pk>/', TheftReportDetailView.as_view(), name='theft_report_detail'),
]