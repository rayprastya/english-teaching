from django.db import models
from django.contrib.auth.models import User
from core.utils.base_model import BaseModel
from django.db.models import Avg, Count, Q
import json
import uuid

# Create your models here.
class Teacher(BaseModel):
    """Teacher profile for managing students"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    name = models.CharField(max_length=200)
    email = models.EmailField()
    school = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.user.username})"

class TeacherReferral(BaseModel):
    """Referral codes created by teachers for student monitoring"""
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='referrals')
    code = models.CharField(max_length=20, unique=True, db_index=True)
    name = models.CharField(max_length=200, help_text="Name/description for this referral")
    class_name = models.CharField(max_length=100, blank=True, help_text="Class or group name")
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")
    
    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_unique_code()
        super().save(*args, **kwargs)
    
    def generate_unique_code(self):
        """Generate a unique 8-character referral code"""
        while True:
            code = str(uuid.uuid4()).replace('-', '')[:8].upper()
            if not TeacherReferral.objects.filter(code=code).exists():
                return code
    
    def get_students_count(self):
        """Get number of students using this referral"""
        return self.student_enrollments.count()
    
    def get_total_attempts(self):
        """Get total attempts by students using this referral"""
        from .models import Message
        return Message.objects.filter(
            room__user__student_enrollments__referral=self,
            role='user',
            spelling_score__isnull=False
        ).count()
    
    def get_average_score(self):
        """Get average score of students using this referral"""
        from .models import Message
        avg = Message.objects.filter(
            room__user__student_enrollments__referral=self,
            role='user',
            spelling_score__isnull=False
        ).aggregate(avg=Avg('spelling_score'))['avg']
        return round(avg, 2) if avg else 0
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class StudentEnrollment(BaseModel):
    """Links students to teacher referrals"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_enrollments')
    referral = models.ForeignKey(TeacherReferral, on_delete=models.CASCADE, related_name='student_enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'referral']
    
    def __str__(self):
        return f"{self.user.username} -> {self.referral.code}"

class Room(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    title = models.CharField(max_length=255, default="New Chat")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username}'s chat - {self.title}"

class ConversationTopic(BaseModel):
    """Topics that can be used to generate conversations"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    difficulty_level = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.name} ({self.get_difficulty_level_display()})"

class UserProgress(BaseModel):
    """Track user progress through conversations"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='progress')
    completed_conversations = models.IntegerField(default=0)
    current_level = models.CharField(max_length=10, choices=ConversationTopic.DIFFICULTY_CHOICES, default='easy')
    
    def get_current_level_display_name(self):
        """Get human-readable current level"""
        return dict(ConversationTopic.DIFFICULTY_CHOICES)[self.current_level]
    
    def get_available_difficulty_levels(self):
        """Get list of difficulty levels available to the user"""
        if self.completed_conversations < 2:  # Changed from 5 to 2
            return ['easy']
        elif self.completed_conversations < 5:  # Changed from 10 to 5
            return ['easy', 'medium']
        else:
            return ['easy', 'medium', 'hard']
    
    def should_advance_level(self):
        """Check if user should advance to next level"""
        if self.completed_conversations >= 2 and self.current_level == 'easy':  # Changed from 5 to 2
            return 'medium'
        elif self.completed_conversations >= 5 and self.current_level == 'medium':  # Changed from 10 to 5
            return 'hard'
        return None
    
    def advance_level_if_needed(self):
        """Advance to next level if criteria met"""
        next_level = self.should_advance_level()
        if next_level:
            self.current_level = next_level
            self.save()
            return True
        return False
    
    def increment_completed_conversations(self):
        """Increment completed conversations count and check for level advance"""
        self.completed_conversations += 1
        level_advanced = self.advance_level_if_needed()
        self.save()
        return level_advanced
    
    def get_average_score(self):
        """Calculate average spelling score for this user"""
        from .models import Message
        avg_score = Message.objects.filter(
            room__user=self.user,
            role='user',
            spelling_score__isnull=False
        ).aggregate(avg_score=Avg('spelling_score'))['avg_score']
        return round(avg_score, 2) if avg_score else 0
    
    def get_total_attempts(self):
        """Get total number of user responses with scores"""
        from .models import Message
        return Message.objects.filter(
            room__user=self.user,
            role='user',
            spelling_score__isnull=False
        ).count()
    
    def get_score_distribution(self):
        """Get score distribution (excellent, good, needs improvement)"""
        from .models import Message
        messages = Message.objects.filter(
            room__user=self.user,
            role='user',
            spelling_score__isnull=False
        )
        
        total = messages.count()
        if total == 0:
            return {'excellent': 0, 'good': 0, 'needs_improvement': 0}
            
        excellent = messages.filter(spelling_score__gte=90).count()
        good = messages.filter(spelling_score__gte=70, spelling_score__lt=90).count()
        needs_improvement = messages.filter(spelling_score__lt=70).count()
        
        return {
            'excellent': round((excellent / total) * 100, 1),
            'good': round((good / total) * 100, 1),
            'needs_improvement': round((needs_improvement / total) * 100, 1)
        }
    
    def get_recent_performance(self, days=7):
        """Get average score for recent days"""
        from django.utils import timezone
        from datetime import timedelta
        from .models import Message
        
        recent_date = timezone.now() - timedelta(days=days)
        avg_score = Message.objects.filter(
            room__user=self.user,
            role='user',
            spelling_score__isnull=False,
            created_at__gte=recent_date
        ).aggregate(avg_score=Avg('spelling_score'))['avg_score']
        return round(avg_score, 2) if avg_score else 0

    def __str__(self):
        return f"{self.user.username} - Level: {self.get_current_level_display_name()}, Completed: {self.completed_conversations}"

class Dialogue(BaseModel):
    """AI-generated dialogue for a specific topic"""
    topic = models.ForeignKey(ConversationTopic, on_delete=models.CASCADE, related_name='dialogues')
    exchanges = models.JSONField()  # Store the dialogue exchanges as JSON
    total_exchanges = models.IntegerField(default=7)
    
    def get_exchanges(self):
        """Get the dialogue exchanges as a Python list"""
        return self.exchanges if isinstance(self.exchanges, list) else []
    
    def set_exchanges(self, exchanges_list):
        """Set the dialogue exchanges from a Python list"""
        self.exchanges = exchanges_list
    
    def __str__(self):
        return f"Dialogue for {self.topic.name}"

class ConversationSession(BaseModel):
    """Tracks user progress through a dialogue"""
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='conversation_sessions')
    dialogue = models.ForeignKey(Dialogue, on_delete=models.CASCADE)
    current_exchange_index = models.IntegerField(default=0)
    is_completed = models.BooleanField(default=False)
    
    def get_current_exchange(self):
        """Get the current exchange the user should respond to"""
        exchanges = self.dialogue.get_exchanges()
        if not self.is_completed and self.current_exchange_index < len(exchanges):
            return exchanges[self.current_exchange_index]
        return None
    
    def advance_to_next_exchange(self):
        """Move to the next exchange in the dialogue"""
        exchanges = self.dialogue.get_exchanges()
        self.current_exchange_index += 1
        if self.current_exchange_index >= len(exchanges):
            self.is_completed = True
            self.save()
        return self.current_exchange_index
    
    def __str__(self):
        return f"Session for {self.dialogue.topic.name} - Exchange {self.current_exchange_index + 1}"

class Message(BaseModel):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='messages', db_index=True)
    content = models.TextField()
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    spelling_score = models.FloatField(null=True, blank=True)
    original_text = models.TextField(null=True, blank=True)
    conversation_session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')

    class Meta:
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['role', 'created_at']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
