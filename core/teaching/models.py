from django.db import models
from django.contrib.auth.models import User
from core.utils.base_model import BaseModel
import json

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

class ConversationTopic(BaseModel):
    """Topics that can be used to generate conversations"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

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
        if self.current_exchange_index < len(exchanges):
            return exchanges[self.current_exchange_index]
        return None
    
    def advance_to_next_exchange(self):
        """Move to the next exchange in the dialogue"""
        self.current_exchange_index += 1
        if self.current_exchange_index >= len(self.dialogue.get_exchanges()):
            self.is_completed = True
        self.save()
    
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
