from django.db import models
import uuid

# Create your models here.

class Position(models.Model):
    title = models.CharField(max_length=50)

    id = models.UUIDField(primary_key=True,default=uuid.uuid4,unique=True,editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    class Meta:
        ordering = ['title']
        indexes = [
            models.Index(fields=['title'])
        ]
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'

    def __str__(self):
        return self.title
    
class JobPosting(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='postings')
    title_override = models.CharField(max_length=120, blank=True)
    department = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    required_experience = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=15,
        choices=[
            ('open', 'Open'),
            ('closed', 'Closed'),
        ],
        default='open'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'

    def __str__(self):
        return self.display_title

    @property
    def display_title(self):
        return self.title_override or self.position.title


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
    job_posting = models.ForeignKey(JobPosting,on_delete=models.CASCADE,related_name='skill_requirements')
    skill = models.ForeignKey(Skill,on_delete=models.CASCADE)
    is_mandatory = models.BooleanField(default=True)

    class Meta:
        ordering = ['job_posting','skill']
        unique_together = ('job_posting','skill')

        verbose_name = 'Skill Requirement'
        verbose_name_plural = 'Skill Requirements'

    def __str__(self):
        return self.job_posting.display_title +' | ' + self.skill.title + ' | ' + ('required' if self.is_mandatory else 'optional')


class Resume(models.Model):
    job_posting = models.ForeignKey('JobPosting', on_delete=models.CASCADE, related_name='resumes')
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
        return f"{self.name or 'Unknown'} - {self.job_posting.display_title}"
