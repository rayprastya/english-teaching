from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Room, Message
from core.utils.whisper import transcribe_audio
import json
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
import tempfile
import os
import random
from core.utils.levenshtein import levenshtein_distance

class RoomView(LoginRequiredMixin, View):
    template_name = 'room.html'

    def get(self, request, room_id=None):
        # Get all rooms for the user
        user_rooms = Room.objects.filter(user=request.user).order_by('-created_at')
        
        if room_id:
            # Get specific room
            room = get_object_or_404(
                Room.objects.select_related('user'),
                id=room_id,
                user=request.user
            )
            # Get last 50 messages ordered by creation time
            messages = room.messages.all().order_by('-created_at')[:100][::-1]
        else:
            # No room selected, show welcome state
            room = None
            messages = None

        context = {
            'room': room,
            'messages': messages,
            'user_rooms': user_rooms,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        title = request.POST.get('title', 'New Chat')
        room = Room.objects.create(user=request.user, title=title)
        return redirect('room_detail', room_id=room.id)

class MessageView(LoginRequiredMixin, View):
    """
    Class-based view for handling message operations.
    Handles both sending messages and processing speech input.
    """
    
    def get_room(self, room_id):
        """Helper method to get room with proper permissions"""
        return get_object_or_404(Room, id=room_id, user=self.request.user)

    def calculate_spelling_score(self, user_input, expected_word):
        """Calculate spelling similarity score between user input and expected word."""
        if not user_input or not expected_word:
            return None
            
        # Calculate Levenshtein distance
        distance = levenshtein_distance(user_input, expected_word)
        max_length = max(len(user_input), len(expected_word))
        
        # Calculate similarity score (0-100)
        if max_length == 0:
            return 0
        similarity = (1 - distance / max_length) * 100
        return round(similarity)

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, room_id=None):
        try:
            room = self.get_room(room_id)
            if not room:
                return JsonResponse({'error': 'Room not found'}, status=404)

            # Handle word generation request
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                if data.get('action') == 'generate_words':
                    # Generate a random word (you can replace this with your word generation logic)
                    words = ['apple', 'banana', 'orange', 'grape', 'mango']
                    word = random.choice(words)
                    message = Message.objects.create(
                        room=room,
                        role='assistant',
                        content=word,
                        original_text=word  # Store the word as original_text
                    )
                    return JsonResponse({
                        'assistant_message': {
                            'role': 'assistant',
                            'content': word
                        }
                    })

            # Handle regular message or audio
            if 'audio' in request.FILES:
                audio_file = request.FILES['audio']
                
                # Get the last assistant message to get the expected word
                last_assistant_message = room.messages.filter(role='assistant').order_by('-created_at').first()
                expected_word = last_assistant_message.original_text if last_assistant_message else None
                
                # Process audio file
                temp_file = None
                try:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
                    for chunk in audio_file.chunks():
                        temp_file.write(chunk)
                    temp_file.close()
                    
                    # Convert audio to text using Whisper
                    text = transcribe_audio(temp_file.name)

                    # Calculate spelling score if expected word is provided
                    spelling_score = None
                    if expected_word:
                        spelling_score = self.calculate_spelling_score(text.lower(), expected_word.lower())

                    # Create assistant response
                    if spelling_score is not None:
                        if spelling_score < 70:
                            response = f"Your pronunciation: {text}\nSpelling Score: {spelling_score}%\nYour pronunciation is almost correct, please try saying '{expected_word}' again!"
                        else:
                            # Generate new word since pronunciation was good
                            words = ['apple', 'banana', 'orange', 'grape', 'mango']
                            new_word = random.choice(words)
                            response = f"Your pronunciation: {text}\nSpelling Score: {spelling_score}%\nGreat pronunciation! Now try saying: {new_word}"
                            expected_word = new_word  # Update expected word for next attempt
                    else:
                        response = f"Your pronunciation: {text}"

                    # Create user message
                    user_message = Message.objects.create(
                        room=room,
                        role='user',
                        content=text,
                        original_text=text
                    )
                    
                    assistant_message = Message.objects.create(
                        room=room,
                        role='assistant',
                        content=response,
                        spelling_score=spelling_score,
                        original_text=expected_word
                    )

                    return JsonResponse({
                        'user_message': {
                            'role': 'user',
                            'content': text,
                            'original_text': text,
                            'spelling_score': spelling_score
                        },
                        'assistant_message': {
                            'role': 'assistant',
                            'content': response
                        }
                    })
                finally:
                    # Clean up the temporary file
                    if temp_file and os.path.exists(temp_file.name):
                        try:
                            os.unlink(temp_file.name)
                        except Exception as e:
                            print(f"Error deleting temporary file: {str(e)}")
            else:
                # Handle text message
                data = json.loads(request.body)
                content = data.get('content')
                
                # Get the last assistant message to get the expected word
                last_assistant_message = room.messages.filter(role='assistant').order_by('-created_at').first()
                expected_word = last_assistant_message.original_text if last_assistant_message else None

                if not content:
                    return JsonResponse({'error': 'No content provided'}, status=400)

                # Calculate spelling score if expected word is provided
                spelling_score = None
                if expected_word:
                    spelling_score = self.calculate_spelling_score(content.lower(), expected_word.lower())

                # Create assistant response
                if spelling_score is not None:
                    if spelling_score < 70:
                        response = f"Your input: {content}\nSpelling Score: {spelling_score}%\nYour pronunciation is almost correct, please try saying '{expected_word}' again!"
                    else:
                        # Generate new word since pronunciation was good
                        words = ['apple', 'banana', 'orange', 'grape', 'mango']
                        new_word = random.choice(words)
                        response = f"Your input: {content}\nSpelling Score: {spelling_score}%\nGreat pronunciation! Now try saying: {new_word}"
                        expected_word = new_word  # Update expected word for next attempt
                else:
                    response = f"Your input: {content}"
                
                user_message = Message.objects.create(
                    room=room,
                    role='user',
                    content=content,
                    spelling_score=spelling_score
                )

                assistant_message = Message.objects.create(
                    room=room,
                    role='assistant',
                    content=response,
                    spelling_score=spelling_score,
                    original_text=expected_word
                )

                return JsonResponse({
                    'user_message': {
                        'role': 'user',
                        'content': content,
                        'spelling_score': spelling_score
                    },
                    'assistant_message': {
                        'role': 'assistant',
                        'content': response
                    }
                })

        except Exception as e:
            print(f"Error in post method: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                login(request, user)
                if not remember_me:
                    request.session.set_expiry(0)
                return redirect('room')
            else:
                return render(request, 'login.html', {
                    'error_message': 'Invalid email or password'
                })
        except User.DoesNotExist:
            return render(request, 'login.html', {
                'error_message': 'Invalid email or password'
            })
    
    return render(request, 'login.html')

@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')

        if password != password_confirm:
            return render(request, 'signup.html', {
                'error_message': 'Passwords do not match'
            })

        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {
                'error_message': 'Email already exists'
            })

        try:
            # Create username from email
            username = email.split('@')[0]
            base_username = username
            counter = 1
            
            # Ensure unique username
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1

            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=name.split()[0] if name else '',
                last_name=' '.join(name.split()[1:]) if name and len(name.split()) > 1 else ''
            )
            
            login(request, user)
            return redirect('room')
        except Exception as e:
            return render(request, 'signup.html', {
                'error_message': 'An error occurred while creating your account'
            })
    
    return render(request, 'signup.html')

@require_http_methods(["GET"])
def logout_view(request):
    logout(request)
    return redirect('login')
