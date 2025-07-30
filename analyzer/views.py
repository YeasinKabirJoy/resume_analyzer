from math import ceil
from django.shortcuts import redirect, render
from .models import *
from django.db.models import Count,Avg
from .forms import JobRoleForm
from utils.analyze import analyze_resume
from utils.pdf_parser import extract_text_from_pdf
from utils.experiance_calculate import calculate_total_experience
from utils.final_score import calculate_final_score
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
        minimum_expreience_years = job_role.minimum_expreience
        mandatory = job_role.skill_requirements.filter(is_mandatory=True).values_list('skill__title', flat=True)
        mandatory_skills = list(mandatory)
        
        optional = job_role.skill_requirements.filter(is_mandatory=False).values_list('skill__title', flat=True)
        optional_skills = list(optional)
        resume = request.FILES.get('file')

        obj = Resume.objects.create(job_role=job_role,resume=resume)
        resume_text = extract_text_from_pdf(obj.resume.path)
        analyzed_response = analyze_resume(resume_text,mandatory_skills,optional_skills)
        total_experience,individual_experience_years = calculate_total_experience(analyzed_response['experiences'])

        experience_details = analyzed_response["experiences"]

        for i in range(0,len(individual_experience_years)):
            _ = experience_details[i]
            _['duration'] = individual_experience_years[i]

        matched_mandatory_skills = analyzed_response["matched_mandatory"]
        missed_mandatory_skills = analyzed_response["missing_mandatory"]
        matched_optional_skills = analyzed_response["missing_mandatory"]
        missed_optional_skills = analyzed_response["missing_optional"]

        obj.name = analyzed_response["name"]
        obj.email = analyzed_response["email"]
        obj.phone = analyzed_response["phone"]
        obj.github = analyzed_response['github']
        obj.linkedin = analyzed_response["linkedin"]
        obj.skills = analyzed_response["skills"]
        obj.experiences = experience_details
        obj.total_experience = total_experience
        obj.matched_mandatory_skills = matched_mandatory_skills
        obj.missed_mandatory_skills = missed_mandatory_skills
        obj.matched_optional_skills = matched_optional_skills
        obj.missed_optional_skills = missed_optional_skills
        
        final = calculate_final_score(
            total_experience,
            minimum_expreience_years,
            matched_mandatory_skills,
            missed_mandatory_skills,
            matched_optional_skills,
            missed_optional_skills
            )
        obj.score = ceil(final["score"])
        obj.verdict = final["status"]
        obj.reason = final["reason"]

        obj.save()

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


def job_create(request):
    if request.method == "POST":
        title = request.POST.get('title')
        minimum_experience = request.POST.get('minimum_experience')
        active = request.POST.get('active')
        mandatory_skills = request.POST.getlist('mandatory_skills')
        optional_skills = request.POST.getlist('optional_skills')
      
        job_role = JobRole.objects.create(
            title=title,
            minimum_expreience=float(minimum_experience),
            active =  True if active == "on" else False
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
    if request.method == "POST":
        title =  request.POST.get('skill_name')
        Skill.objects.create(title=title)
    skills = Skill.objects.all()
    context = {
        'skills':skills,
    }
    return render(request,'skill.html',context)


def skill_edit(request):
    if request.method == "POST":
        id =  request.POST.get('skill_id')
        title =  request.POST.get('skill_name')
        obj = Skill.objects.get(id=id)
        obj.title = title
        obj.save()
    skills = Skill.objects.all()
    context = {
        'skills':skills,
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