from django.db import models
from django.contrib.auth.models import User
from core.utils.base_model import BaseModel

# Create your models here.
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

    class Meta:
        indexes = [
            models.Index(fields=['room', 'created_at']),
            models.Index(fields=['role', 'created_at']),
        ]
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
