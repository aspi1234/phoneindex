from django.urls import path
from .views import (RegisterDeviceView, 
                    UserDeviceListView, 
                    ReportDeviceStolenView,
                    TheftReportDetailView,
                    VerifyDeviceView,
                    ReportFoundDeviceView,
                    UserTheftReportListView,
                    FoundReportOwnerDetailView,
                    DeleteDeviceView) # Import ReportDeviceStolenView

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
    path('verify-imei/', VerifyDeviceView.as_view(), name='verify_device_imei'),
    # --- NEW URL FOR REPORTING A FOUND DEVICE (PUBLIC) ---
    path('report-found/', ReportFoundDeviceView.as_view(), name='report_found_device'),
    # --- NEW URL FOR USER'S THEFT REPORT LIST ("MY CASES") ---
    path('my-theft-reports/', UserTheftReportListView.as_view(), name='user_theft_report_list'),
    # --- NEW URL FOR OWNER TO VIEW A SPECIFIC FOUND REPORT ---
    # pk here is the primary key of the FoundReport instance
    path('found-report/<int:pk>/view/', FoundReportOwnerDetailView.as_view(), name='found_report_owner_detail'), # --- NEW URL FOR DELETING A REGISTERED DEVICE ---
    # pk here is the primary key of the RegisteredDevice instance
    path('device/<int:pk>/delete/', DeleteDeviceView.as_view(), name='delete_device'),
    ]