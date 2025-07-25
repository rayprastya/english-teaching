from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Avg, Count
from django.contrib.auth import login
from django.views.decorators.http import require_http_methods
from .models import Teacher, TeacherReferral, StudentEnrollment, Message, UserProgress
from django.contrib.auth.models import User

class TeacherDashboardView(LoginRequiredMixin, View):
    template_name = 'teacher/dashboard.html'
    
    def get(self, request):
        # Check if user is a teacher
        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            messages.error(request, "You need teacher access to view this page.")
            return redirect('room_list')
        
        # Get teacher's referrals
        referrals = TeacherReferral.objects.filter(teacher=teacher).order_by('-created_at')
        
        # Calculate statistics
        total_referrals = referrals.count()
        active_referrals = referrals.filter(is_active=True).count()
        total_students = StudentEnrollment.objects.filter(referral__teacher=teacher).count()
        
        # Get recent activity
        recent_enrollments = StudentEnrollment.objects.filter(
            referral__teacher=teacher
        ).select_related('user', 'referral').order_by('-enrolled_at')[:10]
        
        context = {
            'teacher': teacher,
            'referrals': referrals,
            'total_referrals': total_referrals,
            'active_referrals': active_referrals,
            'total_students': total_students,
            'recent_enrollments': recent_enrollments,
        }
        
        return render(request, self.template_name, context)

class CreateReferralView(LoginRequiredMixin, View):
    def post(self, request):
        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            return JsonResponse({'error': 'Teacher access required'}, status=403)
        
        name = request.POST.get('name', '').strip()
        class_name = request.POST.get('class_name', '').strip()
        
        if not name:
            messages.error(request, "Referral name is required.")
            return redirect('teacher_dashboard')
        
        # Create new referral
        referral = TeacherReferral.objects.create(
            teacher=teacher,
            name=name,
            class_name=class_name
        )
        
        messages.success(request, f"Referral code '{referral.code}' created successfully!")
        return redirect('teacher_dashboard')

class ReferralDetailView(LoginRequiredMixin, View):
    template_name = 'teacher/referral_detail.html'
    
    def get(self, request, referral_id):
        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            messages.error(request, "You need teacher access to view this page.")
            return redirect('room_list')
        
        referral = get_object_or_404(TeacherReferral, id=referral_id, teacher=teacher)
        
        # Get students using this referral
        enrollments = StudentEnrollment.objects.filter(
            referral=referral
        ).select_related('user').order_by('-enrolled_at')
        
        # Get student performance data
        student_stats = []
        for enrollment in enrollments:
            user = enrollment.user
            
            # Get user progress
            try:
                progress = UserProgress.objects.get(user=user)
            except UserProgress.DoesNotExist:
                progress = None
            
            # Calculate student's scores
            messages_with_scores = Message.objects.filter(
                room__user=user,
                role='user',
                spelling_score__isnull=False
            )
            
            total_attempts = messages_with_scores.count()
            avg_score = messages_with_scores.aggregate(avg=Avg('spelling_score'))['avg']
            avg_score = round(avg_score, 2) if avg_score else 0
            
            # Recent performance (last 7 days)
            from django.utils import timezone
            from datetime import timedelta
            recent_date = timezone.now() - timedelta(days=7)
            recent_attempts = messages_with_scores.filter(created_at__gte=recent_date)
            recent_avg = recent_attempts.aggregate(avg=Avg('spelling_score'))['avg']
            recent_avg = round(recent_avg, 2) if recent_avg else 0
            
            student_stats.append({
                'enrollment': enrollment,
                'user': user,
                'progress': progress,
                'total_attempts': total_attempts,
                'avg_score': avg_score,
                'recent_avg': recent_avg,
                'recent_attempts': recent_attempts.count()
            })
        
        context = {
            'teacher': teacher,
            'referral': referral,
            'student_stats': student_stats,
        }
        
        return render(request, self.template_name, context)

class ToggleReferralView(LoginRequiredMixin, View):
    def post(self, request, referral_id):
        try:
            teacher = request.user.teacher_profile
        except Teacher.DoesNotExist:
            return JsonResponse({'error': 'Teacher access required'}, status=403)
        
        referral = get_object_or_404(TeacherReferral, id=referral_id, teacher=teacher)
        referral.is_active = not referral.is_active
        referral.save()
        
        status = "activated" if referral.is_active else "deactivated"
        messages.success(request, f"Referral code '{referral.code}' has been {status}.")
        
        return redirect('teacher_dashboard')

@require_http_methods(["GET", "POST"])
def teacher_signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        school = request.POST.get('school', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        # Validation
        if not all([name, username, email, password, password_confirm]):
            return render(request, 'teacher_signup.html', {
                'error_message': 'Please fill in all required fields'
            })

        if password != password_confirm:
            return render(request, 'teacher_signup.html', {
                'error_message': 'Passwords do not match'
            })

        if len(password) < 6:
            return render(request, 'teacher_signup.html', {
                'error_message': 'Password must be at least 6 characters long'
            })

        # Check if username or email already exists
        if User.objects.filter(username=username).exists():
            return render(request, 'teacher_signup.html', {
                'error_message': 'Username already exists'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'teacher_signup.html', {
                'error_message': 'Email already registered'
            })

        try:
            # Create user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name.split(' ')[0] if ' ' in name else name,
                last_name=' '.join(name.split(' ')[1:]) if ' ' in name else ''
            )

            # Create teacher profile
            teacher = Teacher.objects.create(
                user=user,
                name=name,
                email=email,
                school=school or ''
            )

            # Auto-login the teacher
            login(request, user)
            
            messages.success(request, f"Welcome {name}! Your teacher account has been created successfully.")
            return redirect('teacher_dashboard')

        except Exception as e:
            return render(request, 'teacher_signup.html', {
                'error_message': f'Error creating account: {str(e)}'
            })

    return render(request, 'teacher_signup.html')