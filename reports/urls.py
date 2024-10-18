from django.urls import path
from . import views

app_name = "report"

urlpatterns = [
    path("create/", views.ReportCreateView.as_view(), name="report-create"),
]
