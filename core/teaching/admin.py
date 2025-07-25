from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Room, Message, ConversationTopic, Dialogue, ConversationSession, UserProgress

# Register your models here.

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'user', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'user__username']

class ScoreRangeFilter(admin.SimpleListFilter):
    title = 'Score Range'
    parameter_name = 'score_range'
    
    def lookups(self, request, model_admin):
        return (
            ('excellent', 'Excellent (90%+)'),
            ('good', 'Good (70-89%)'),
            ('needs_improvement', 'Needs Improvement (<70%)'),
            ('no_score', 'No Score'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'excellent':
            return queryset.filter(spelling_score__gte=90)
        elif self.value() == 'good':
            return queryset.filter(spelling_score__gte=70, spelling_score__lt=90)
        elif self.value() == 'needs_improvement':
            return queryset.filter(spelling_score__lt=70)
        elif self.value() == 'no_score':
            return queryset.filter(spelling_score__isnull=True)
        return queryset

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'room', 'user_name', 'role', 'content_preview', 'score_with_color', 'created_at']
    list_filter = ['role', 'created_at', ScoreRangeFilter]
    search_fields = ['content', 'room__title', 'room__user__username']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'
    
    def user_name(self, obj):
        return obj.room.user.username
    user_name.short_description = 'Student'
    
    def score_with_color(self, obj):
        if obj.spelling_score is None:
            return "N/A"
        score = obj.spelling_score
        if score >= 90:
            return f"🟢 {score}%"
        elif score >= 70:
            return f"🟡 {score}%"
        else:
            return f"🔴 {score}%"
    score_with_color.short_description = 'Score'
    

@admin.register(ConversationTopic)
class ConversationTopicAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'difficulty_level', 'description', 'is_active', 'created_at']
    list_filter = ['difficulty_level', 'is_active', 'created_at']
    search_fields = ['name', 'description']

@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'completed_conversations', 'current_level', 'average_score', 'total_attempts', 'recent_performance', 'performance_trend', 'created_at']
    list_filter = ['current_level', 'completed_conversations', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'score_breakdown']
    
    def average_score(self, obj):
        score = obj.get_average_score()
        if score >= 90:
            return f"🟢 {score}%"
        elif score >= 70:
            return f"🟡 {score}%"
        else:
            return f"🔴 {score}%" if score > 0 else "No scores yet"
    average_score.short_description = 'Avg Score'
    
    def total_attempts(self, obj):
        return obj.get_total_attempts()
    total_attempts.short_description = 'Total Attempts'
    
    def recent_performance(self, obj):
        score = obj.get_recent_performance()
        return f"{score}%" if score > 0 else "No recent activity"
    recent_performance.short_description = 'Last 7 Days'
    
    def performance_trend(self, obj):
        recent = obj.get_recent_performance()
        overall = obj.get_average_score()
        if recent == 0 or overall == 0:
            return "📊 No data"
        elif recent > overall + 5:
            return "📈 Improving"
        elif recent < overall - 5:
            return "📉 Declining"
        else:
            return "➡️ Stable"
    performance_trend.short_description = 'Trend'
    
    def score_breakdown(self, obj):
        dist = obj.get_score_distribution()
        return f"Excellent (90%+): {dist['excellent']}% | Good (70-89%): {dist['good']}% | Needs Improvement (<70%): {dist['needs_improvement']}%"
    score_breakdown.short_description = 'Score Distribution'

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

# Add custom admin site modifications
admin.site.site_header = "English Teaching Admin"
admin.site.site_title = "English Teaching Admin Portal"
admin.site.index_title = "Welcome to English Teaching Administration"

# Add custom link to admin index
def admin_index_view(request, extra_context=None):
    """Custom admin index view with analytics link"""
    extra_context = extra_context or {}
    extra_context['analytics_url'] = reverse('score_analytics')
    return admin.site.index(request, extra_context)

admin.site.index = admin_index_view
