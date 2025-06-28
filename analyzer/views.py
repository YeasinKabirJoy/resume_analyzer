from django.shortcuts import redirect, render
from .models import *
from django.db.models import Count,Avg
from .forms import JobRoleForm
def home(request):
    all_resume = Resume.objects.all()
    average = all_resume.aggregate(average=Avg('score'))['average']
    active_job_count = JobRole.objects.filter(active=True).count()
    resume_count = all_resume.count()
    matches = all_resume.filter(verdict='matched').count()
    skipped = all_resume.filter(verdict='skipped').count()
    over_qualified = all_resume.filter(verdict='overqualified').count()
    context = {
        'resume_count':resume_count,
        'matches':matches,
        'skipped':skipped,
        'over_qualified':over_qualified,
        'active_job_count':active_job_count,
        'average_score':average
    }
    return render(request,'home.html',context)

def resume_upload(request):
    if request.method == "POST":
        pass
    else:
        job_role = JobRole.objects.filter(active=True).order_by('title')
        context = {
            'job_roles':job_role
        }
    return render(request,'resume_upload.html',context)

def result(request,id):
    resume_data = Resume.objects.get(id=id)
    context = {
        "resume": resume_data
    }
    return render(request,'result.html',context)

def jobs(request):
    title = ''
    all = request.GET.get('all') 
    if all and all == 'yes':
        jobs = JobRole.objects.all().order_by('created_at').annotate(resume_count=Count('resume'))
        title = 'All'
    else:
        jobs = JobRole.objects.filter(active=True).order_by('created_at').annotate(resume_count=Count('resume'))
        title = 'Active'
    active_jobs = []

    for job in jobs:
        active_jobs.append({
            'id': job.id,
            'title': job.title,
            'resume_count': job.resume_count,
        })

    context = {
        'active_jobs': active_jobs,
        'title':title
        
        }
    return render(request,'jobs.html',context)

def job_details(request,id):
    job = JobRole.objects.get(id=id)
    context = {
        'job':job
    }
    return render(request,'job_details.html',context)

def job_edit(request,id):
    job = JobRole.objects.get(id=id)
    form = JobRoleForm(instance=job)
    if request.method == "POST":
         form = JobRoleForm(request.POST,instance=job)
         if form.is_valid():
             form.save()
             return redirect('job_details',id=job.id)

    context = {
        'form':form,
        'job':job
    }

    return render(request,'job_edit.html',context)

def resumes(request,id):
    job = JobRole.objects.get(id=id)
    resumes = job.resume_set.all()

    context = {
        'job':job,
        'resumes':resumes
    }
    
    return render(request,'resumes.html',context)