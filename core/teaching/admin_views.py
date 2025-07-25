from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Avg, Count, Q
from django.utils.decorators import method_decorator
from django.views import View
from .models import UserProgress, Message, User
from django.contrib.auth.models import User

@method_decorator(staff_member_required, name='dispatch')
class ScoreAnalyticsView(View):
    template_name = 'admin/teaching/score_analytics.html'
    
    def get(self, request):
        # Overall statistics
        total_students = UserProgress.objects.count()
        total_attempts = Message.objects.filter(role='user', spelling_score__isnull=False).count()
        
        if total_attempts > 0:
            overall_avg_score = Message.objects.filter(
                role='user', 
                spelling_score__isnull=False
            ).aggregate(avg=Avg('spelling_score'))['avg']
            overall_avg_score = round(overall_avg_score, 2) if overall_avg_score else 0
        else:
            overall_avg_score = 0
        
        # Performance distribution
        excellent_count = Message.objects.filter(
            role='user', 
            spelling_score__gte=90
        ).count()
        good_count = Message.objects.filter(
            role='user', 
            spelling_score__gte=70, 
            spelling_score__lt=90
        ).count()
        needs_improvement_count = Message.objects.filter(
            role='user', 
            spelling_score__lt=70
        ).count()
        
        # Top performers
        top_performers = []
        for progress in UserProgress.objects.select_related('user').all():
            avg_score = progress.get_average_score()
            if avg_score > 0:
                top_performers.append({
                    'user': progress.user,
                    'score': avg_score,
                    'attempts': progress.get_total_attempts()
                })
        
        top_performers.sort(key=lambda x: x['score'], reverse=True)
        top_performers = top_performers[:10]  # Top 10
        
        # Students needing help
        students_needing_help = []
        for progress in UserProgress.objects.select_related('user').all():
            avg_score = progress.get_average_score()
            attempts = progress.get_total_attempts()
            if 0 < avg_score < 70 and attempts >= 5:  # At least 5 attempts
                students_needing_help.append({
                    'user': progress.user,
                    'score': avg_score,
                    'attempts': attempts,
                    'recent_performance': progress.get_recent_performance()
                })
        
        students_needing_help.sort(key=lambda x: x['score'])
        
        context = {
            'total_students': total_students,
            'total_attempts': total_attempts,
            'overall_avg_score': overall_avg_score,
            'excellent_count': excellent_count,
            'good_count': good_count,
            'needs_improvement_count': needs_improvement_count,
            'top_performers': top_performers,
            'students_needing_help': students_needing_help,
            'title': 'Student Score Analytics',
        }
        
        return render(request, self.template_name, context)