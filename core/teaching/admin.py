from django.contrib import admin
from .models import Room, Message, ConversationTopic, Dialogue, ConversationSession, UserProgress

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
    search_fields = ['content', 'room__title', 'room__user__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

@admin.register(ConversationTopic)
class ConversationTopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'difficulty_level', 'description', 'is_active', 'created_at']
    list_filter = ['difficulty_level', 'is_active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'completed_conversations', 'current_level', 'available_levels', 'created_at']
    list_filter = ['current_level', 'completed_conversations', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    
    def available_levels(self, obj):
        return ', '.join(obj.get_available_difficulty_levels())
    available_levels.short_description = 'Available Levels'

@admin.register(Dialogue)
class DialogueAdmin(admin.ModelAdmin):
    list_display = ['id', 'topic', 'total_exchanges', 'created_at']
    list_filter = ['topic__difficulty_level', 'total_exchanges', 'created_at']
    search_fields = ['topic__name']

@admin.register(ConversationSession)
class ConversationSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'dialogue_topic', 'dialogue_difficulty', 'current_exchange_index', 'total_exchanges', 'is_completed', 'created_at']
    list_filter = ['is_completed', 'dialogue__topic__difficulty_level', 'created_at']
    search_fields = ['room__title', 'dialogue__topic__name']
    
    def dialogue_topic(self, obj):
        return obj.dialogue.topic.name
    dialogue_topic.short_description = 'Topic'
    
    def dialogue_difficulty(self, obj):
        return obj.dialogue.topic.get_difficulty_level_display()
    dialogue_difficulty.short_description = 'Difficulty'
    
    def total_exchanges(self, obj):
        return obj.dialogue.total_exchanges
    total_exchanges.short_description = 'Total Exchanges'
