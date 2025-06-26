from django.urls import path
from .views import home,resume_upload,result,jobs
urlpatterns = [
    path('upload/', resume_upload),
    path('result/',result),
    path('',home),
    path('jobs/',jobs)
]
