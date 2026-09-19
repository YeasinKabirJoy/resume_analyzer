from django.shortcuts import redirect, render
from .models import *
from django.db.models import Count,Avg
from .forms import JobPostingForm, PositionForm, SkillForm
from django.utils import timezone
from services.pipeline import process_resume
from django.http import HttpResponse
import fitz
from io import BytesIO


def home(request):
    all_resume = Resume.objects.all()
    average = all_resume.aggregate(average=Avg('score'))['average']
    active_job_count = JobPosting.objects.filter(status='open').count()
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
        job_posting_id = request.POST.get('job_posting')
        job_posting = JobPosting.objects.get(id=job_posting_id)
        uploaded_files = request.FILES.getlist('file')

        if not uploaded_files:
            return redirect('resume_upload')

        print("BULK RESUME UPLOAD STARTED")
        print(f"Target job: {job_posting.display_title}")
        print(f"File count: {len(uploaded_files)}")

        bulk_results = []
        for uploaded_file in uploaded_files:
            print(f"PROCESSING FILE: {uploaded_file.name}")
            obj = Resume.objects.create(job_posting=job_posting, resume=uploaded_file)
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
            bulk_results.append({
                "id": obj.id,
                "name": obj.name,
                "file_name": uploaded_file.name,
                "status": obj.status,
                "verdict": obj.verdict,
                "score": obj.score,
                "confidence_score": obj.confidence_score,
                "error_message": obj.error_message,
            })
            print(f"FINISHED FILE: {uploaded_file.name} | status={obj.status} | score={obj.score}")

        if len(uploaded_files) == 1:
            return redirect('result', id=bulk_results[0]["id"])

        print("BULK RESUME UPLOAD SUMMARY:")
        print({
            "job": job_posting.display_title,
            "total": len(bulk_results),
            "completed": sum(1 for item in bulk_results if item["status"] == "completed"),
            "failed": sum(1 for item in bulk_results if item["status"] == "failed"),
        })

        context = {
            "job_posting": job_posting,
            "results": bulk_results,
            "completed_count": sum(1 for item in bulk_results if item["status"] == "completed"),
            "failed_count": sum(1 for item in bulk_results if item["status"] == "failed"),
        }
        return render(request, "bulk_results.html", context)

    job_postings = JobPosting.objects.filter(status='open').select_related('position').order_by('position__title', '-created_at')
    context = {
        'job_postings':job_postings
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
        jobs = JobPosting.objects.all().select_related('position').order_by('created_at').annotate(resume_count=Count('resumes'))
        title = 'All'
    else:
        jobs = JobPosting.objects.filter(status='open').select_related('position').order_by('created_at').annotate(resume_count=Count('resumes'))
        title = 'Active'
    active_jobs = []

    for job in jobs:
        active_jobs.append({
            'id': job.id,
            'title': job.display_title,
            'position_title': job.position.title,
            'department': job.department,
            'location': job.location,
            'status': job.status,
            'resume_count': job.resume_count,
        })

    context = {
        'active_jobs': active_jobs,
        'title':title
        
        }
    return render(request,'jobs.html',context)

def job_details(request,id):
    job = JobPosting.objects.select_related('position').get(id=id)
    context = {
        'job':job
    }
    return render(request,'job_details.html',context)

def job_edit(request,id):
    job = JobPosting.objects.select_related('position').get(id=id)
    form = JobPostingForm(instance=job)
    if request.method == "POST":
         form = JobPostingForm(request.POST,instance=job)
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
        position_id = request.POST.get('position')
        required_experience = request.POST.get('required_experience')
        department = request.POST.get('department', '').strip()
        location = request.POST.get('location', '').strip()
        status = request.POST.get('status') or 'open'
        mandatory_skills = request.POST.getlist('mandatory_skills')
        optional_skills = request.POST.getlist('optional_skills')
        position = Position.objects.get(id=position_id)
        job_posting = JobPosting.objects.create(
            position=position,
            required_experience=float(required_experience or 0),
            department=department,
            location=location,
            status=status if status in {'open', 'closed'} else 'open',
            title_override='',
        )
        
        for skill in mandatory_skills:
            obj = Skill.objects.get(id=skill)
            SkillRequirements.objects.create(job_posting=job_posting,skill=obj)
        for skill in optional_skills:
            obj = Skill.objects.get(id=skill)
            SkillRequirements.objects.create(job_posting=job_posting,skill=obj,is_mandatory=False)

        return redirect('job_details', id=job_posting.id)

    skills = Skill.objects.all()
    positions = Position.objects.all().order_by('title')
    context = {
        'skills':skills,
        'positions':positions,
    }

    return render(request,'job_create.html',context)

def resumes(request,id):
    job = JobPosting.objects.select_related('position').get(id=id)
    resumes = job.resumes.all()

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


def positions(request):
    form = PositionForm()
    if request.method == "POST":
        form = PositionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('positions')
    positions = Position.objects.all()
    context = {
        'positions': positions,
        'form': form,
    }
    return render(request, 'positions.html', context)


def position_edit(request):
    if request.method == "POST":
        id = request.POST.get('position_id')
        obj = Position.objects.get(id=id)
        form = PositionForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect('positions')
    else:
        form = PositionForm()
    positions = Position.objects.all()
    context = {
        'positions': positions,
        'form': form,
    }
    return render(request, 'positions.html', context)


def position_delete(request):
    if request.method == "POST":
        id = request.POST.get('position_id')
        obj = Position.objects.get(id=id)
        obj.delete()
    positions = Position.objects.all()
    context = {
        'positions': positions,
    }
    return render(request, 'positions.html', context)
