from django.shortcuts import redirect, render
from .models import *
from django.db.models import Count,Avg
from .forms import JobRoleForm, SkillForm
from django.utils import timezone
from services.pipeline import process_resume
from django.http import HttpResponse
import fitz
from io import BytesIO


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
        'average_score':round(average,2) if average else 0.0
    }
    return render(request,'home.html',context)

def resume_upload(request):
    if request.method == "POST":
        job_id = request.POST.get('job_role')
        job_role = JobRole.objects.get(id=job_id)
        resume = request.FILES.get('file')

        obj = Resume.objects.create(job_role=job_role,resume=resume)
        try:
            analyzed_response = process_resume(obj)
            for field, value in analyzed_response.items():
                setattr(obj, field, value)
            obj.status = "completed"
            obj.error_message = None
        except Exception as exc:
            obj.status = "failed"
            obj.error_message = str(exc)
            obj.score = 0
            obj.verdict = "skipped"
            obj.reason = str(exc)
        obj.processed_at = timezone.now()
        obj.save()
        return redirect('result', id=obj.id)

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


def resume_preview(request, id):
    resume_data = Resume.objects.get(id=id)
    pdf_path = resume_data.resume.path

    with fitz.open(pdf_path) as document:
        if document.page_count == 0:
            return HttpResponse(status=404)
        page = document.load_page(0)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
        image_bytes = pixmap.tobytes("png")

    return HttpResponse(image_bytes, content_type="image/png")

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


def job_create(request):
    if request.method == "POST":
        title = request.POST.get('title')
        minimum_experience = request.POST.get('minimum_experience')
        active = request.POST.get('active')
        mandatory_skills = request.POST.getlist('mandatory_skills')
        optional_skills = request.POST.getlist('optional_skills')
      
        job_role = JobRole.objects.create(
            title=title,
            minimum_experience=float(minimum_experience),
            active=True if active == "on" else False
            )
        
        for skill in mandatory_skills:
            obj = Skill.objects.get(id=skill)
            SkillRequirements.objects.create(job_role=job_role,skill=obj)
        for skill in optional_skills:
            obj = Skill.objects.get(id=skill)
            SkillRequirements.objects.create(job_role=job_role,skill=obj,is_mandatory=False)
            
    skills = Skill.objects.all()
    context = {
        'skills':skills,
    }

    return render(request,'job_create.html',context)

def resumes(request,id):
    job = JobRole.objects.get(id=id)
    resumes = job.resume_set.all()

    context = {
        'job':job,
        'resumes':resumes
    }
    
    return render(request,'resumes.html',context)


def skill(request):
    form = SkillForm()
    if request.method == "POST":
        form = SkillForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('skills')
    skills = Skill.objects.all()
    context = {
        'skills':skills,
        'form': form,
    }
    return render(request,'skill.html',context)


def skill_edit(request):
    if request.method == "POST":
        id =  request.POST.get('skill_id')
        obj = Skill.objects.get(id=id)
        form = SkillForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('skills')
    else:
        form = SkillForm()
    skills = Skill.objects.all()
    context = {
        'skills':skills,
        'form': form,
    }
    return render(request,'skill.html',context)


def skill_delete(request):
    if request.method == "POST":
        id =  request.POST.get('skill_id')
        obj = Skill.objects.get(id=id)
        obj.delete()
    skills = Skill.objects.all()
    context = {
        'skills':skills,
    }
    return render(request,'skill.html',context)
