from django.shortcuts import render
from .models import *
from django.db.models import Count

def home(request):
    return render(request,'home.html')

def resume_upload(request):
    if request.method == "POST":
        pass
    else:
        job_role = JobRole.objects.filter(active=True).order_by('title')
        context = {
            'job_roles':job_role
        }
    return render(request,'resume_upload.html',context)

def result(request):
    resume_data = Resume.objects.get(id="28e3777d-2b8a-4ae4-91b3-c52a2434970d")
    context = {
        "resume": resume_data
    }
    return render(request,'result.html',context)

def jobs(request):
    jobs = JobRole.objects.filter(active=True).order_by('created_at').annotate(resume_count=Count('resume'))
    active_jobs = []

    for job in jobs:
        active_jobs.append({
            'id': job.id,
            'title': job.title,
            'resume_count': job.resume_count,
        })
    return render(request,'jobs.html',{'active_jobs': active_jobs})