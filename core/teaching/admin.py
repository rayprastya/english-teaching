from django.contrib import admin
from .models import Room, Message, ConversationTopic, Dialogue, ConversationSession

# Register your models here.

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'user__username']

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'role', 'content_preview', 'spelling_score', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'room__title']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'

@admin.register(ConversationTopic)
class ConversationTopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'description', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(Dialogue)
class DialogueAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'total_exchanges', 'created_at']
    list_filter = ['topic', 'total_exchanges', 'created_at']
    search_fields = ['topic__name']

@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'dialogue_topic', 'current_exchange_index', 'total_exchanges', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'created_at']
    search_fields = ['room__title', 'dialogue__topic__name']
    
    def dialogue_topic(self, obj):
        return obj.dialogue.topic.name
    dialogue_topic.short_description = 'Topic'
    
    def total_exchanges(self, obj):
        return obj.dialogue.total_exchanges
    total_exchanges.short_description = 'Total Exchanges'
