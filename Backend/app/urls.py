
from django.urls import path
from .views import processEmail

urlpatterns = [
    path("processEmail", processEmail, name="processEmail"),
]
