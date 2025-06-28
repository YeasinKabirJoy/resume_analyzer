from django.urls import path
from .views import home,resume_upload,result,jobs,job_details,job_edit,resumes
urlpatterns = [
    path('upload/', resume_upload,name='resume_upload'),
    path('result/<uuid:id>',result,name='result'),
    path('',home,name='home'),
    path('jobs/',jobs,name='active_jobs'),
    path('jobs/<uuid:id>/',job_details,name='job_details'),
    path('jobs/<uuid:id>/',job_details,name='job_details'),
    path('job_edit/<uuid:id>/',job_edit,name='job_edit'),
    path('jobs/<uuid:id>/resume/',resumes,name='resumes')
]
