from django.db import models
import uuid
from django.utils.text import slugify

# Create your models here.

class JobRole(models.Model):
    title = models.CharField(max_length=50)
    minimum_experience = models.PositiveIntegerField(default=0)

    version = models.PositiveIntegerField(blank=True)
    active = models.BooleanField(default=True,blank=True)

    id = models.UUIDField(primary_key=True,default=uuid.uuid4,unique=True,editable=False)
    slug = models.SlugField(max_length=60,unique=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title'])
        ]
        verbose_name = 'Job Role'
        verbose_name_plural = 'Job Roles'

    def __str__(self):
        return f"{self.title}-v{self.version}"
    
    def save(self, *args,**kwargs):
        if self._state.adding and not self.version:
            last = JobRole.objects.filter(title=self.title).order_by('-version').first()
            self.version = last.version + 1 if last else 1
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = slugify(f"{base_slug}-v{self.version}")
        return super().save(*args,**kwargs)
    

class Skill(models.Model):
    title = models.CharField(max_length=50)
    aliases = models.JSONField(default=list, blank=True)
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,unique=True,editable=False)
    
    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title'])
        ]
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'

    def __str__(self):
        return self.title
    
class SkillRequirements(models.Model):
    job_role = models.ForeignKey(JobRole,on_delete=models.CASCADE,related_name='skill_requirements')
    skill = models.ForeignKey(Skill,on_delete=models.CASCADE)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        ordering = ['job_role','skill']
        unique_together = ('job_role','skill')

        verbose_name = 'Skill Requirement'
        verbose_name_plural = 'Skill Requirements'

    def __str__(self):
        return self.job_role.title + '-v' + str(self.job_role.version) +' | ' + self.skill.title + ' | ' + ('required' if self.is_mandatory else '')


class Resume(models.Model):
    job_role = models.ForeignKey('JobRole', on_delete=models.CASCADE)
    resume = models.FileField(upload_to='resumes/')

    name = models.CharField(max_length=255, blank=True,null=True)
    email = models.EmailField(blank=True,null=True)
    phone = models.CharField(max_length=20, blank=True,null=True)
    github = models.URLField(blank=True, null=True)
    linkedin = models.URLField(blank=True,null=True)
    skills = models.JSONField(blank=True, null=True)
    total_experience = models.FloatField(blank=True,default=0.0)  # in years
    confidence_score = models.FloatField(blank=True, null=True)
    text_quality_score = models.FloatField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    score = models.IntegerField(blank=True,null=True)
    reason = models.CharField(max_length=100, blank=True,null=True)
    verdict = models.CharField(max_length=15,choices=[
        ('matched', 'Matched'),
        ('skipped', 'Skipped'),
        ('overqualified', 'Overqualified')
    ], blank=True,default='matched')

    # Structured pipeline outputs
    matched_mandatory_skills = models.JSONField(blank=True, null=True)
    missed_mandatory_skills = models.JSONField(blank=True, null=True)
    matched_optional_skills = models.JSONField(blank=True, null=True)
    missed_optional_skills = models.JSONField(blank=True, null=True)
    experiences = models.JSONField(blank=True, null=True)  # list of dicts: designation, company, duration
    educations = models.JSONField(blank=True, null=True)

    status = models.CharField(
        max_length=15,
        choices=[
            ('pending', 'Pending'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )

    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        ordering = ['-uploaded_at']

        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'

    def __str__(self):
        return f"{self.name or 'Unknown'} - {self.job_role.title}"
