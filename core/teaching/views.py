from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Room, Message, ConversationTopic, Dialogue, ConversationSession
from core.utils.whisper import transcribe_audio
from core.utils.conversation_ai import ConversationAI
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
        
        # Get all available conversation topics
        topics = ConversationTopic.objects.filter(is_active=True).order_by('name')
        
        if room_id:
            # Get specific room
            room = get_object_or_404(
                Room.objects.select_related('user'),
                id=room_id,
                user=request.user
            )
            # Get last 50 messages ordered by creation time
            messages = room.messages.all().order_by('-created_at')[:100][::-1]
            
            # Get current conversation session if any
            current_session = room.conversation_sessions.filter(is_completed=False).first()
        else:
            # No room selected, show welcome state
            room = None
            messages = None
            current_session = None

        # Get current expected response if there's an active session
        current_expected_response = None
        if current_session and not current_session.is_completed:
            current_exchange = current_session.get_current_exchange()
            if current_exchange:
                current_expected_response = current_exchange['user_should_say']

        context = {
            'room': room,
            'messages': messages,
            'user_rooms': user_rooms,
            'topics': topics,
            'current_session': current_session,
            'current_expected_response': current_expected_response,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        title = request.POST.get('title', 'New Chat')
        room = Room.objects.create(user=request.user, title=title)
        return redirect('room_detail', room_id=room.id)

class TopicView(LoginRequiredMixin, View):
    """Handle topic-related operations"""
    
    def post(self, request, room_id):
        """Generate a new conversation for a selected topic"""
        room = get_object_or_404(Room, id=room_id, user=request.user)
        
        try:
            data = json.loads(request.body)
            topic_name = data.get('topic')
            
            if not topic_name:
                return JsonResponse({'error': 'Topic name is required'}, status=400)
            
            # Get or create the topic
            topic, created = ConversationTopic.objects.get_or_create(
                name=topic_name,
                defaults={'description': f'Conversation about {topic_name}'}
            )
            
            # Generate new dialogue using AI
            ai = ConversationAI()
            exchanges = ai.generate_conversation(topic_name, num_exchanges=7)
            
            # Create new dialogue
            dialogue = Dialogue.objects.create(
                topic=topic,
                exchanges=exchanges,
                total_exchanges=len(exchanges)
            )
            
            # End any existing conversation sessions in this room
            ConversationSession.objects.filter(room=room, is_completed=False).update(is_completed=True)
            
            # Create new conversation session
            session = ConversationSession.objects.create(
                room=room,
                dialogue=dialogue,
                current_exchange_index=0
            )
            
            # Get the first exchange
            first_exchange = session.get_current_exchange()
            
            if first_exchange:
                # Create the initial bot message
                Message.objects.create(
                    room=room,
                    role='assistant',
                    content=first_exchange['bot_says'],
                    conversation_session=session,
                    original_text=first_exchange['user_should_say']  # What user should say
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'New conversation started!',
                    'bot_message': first_exchange['bot_says'],
                    'expected_response': first_exchange['user_should_say'],
                    'exchange_number': first_exchange['exchange_number'],
                    'total_exchanges': dialogue.total_exchanges
                })
            else:
                return JsonResponse({'error': 'Failed to generate conversation'}, status=500)
                
        except Exception as e:
            print(f"Error in TopicView: {str(e)}")
            return JsonResponse({'error': 'Failed to generate conversation'}, status=500)

class MessageView(LoginRequiredMixin, View):
    """
    Enhanced message view for handling conversation flow
    """
    
    def get_room(self, room_id):
        """Helper method to get room with proper permissions"""
        return get_object_or_404(Room, id=room_id, user=self.request.user)

    def calculate_spelling_score(self, user_input, expected_text):
        """Calculate spelling similarity score between user input and expected text."""
        if not user_input or not expected_text:
            return None
            
        # Calculate Levenshtein distance
        distance = levenshtein_distance(user_input.lower(), expected_text.lower())
        max_length = max(len(user_input), len(expected_text))
        
        # Calculate similarity score (0-100)
        if max_length == 0:
            return 0
        similarity = (1 - distance / max_length) * 100
        return round(similarity)

    def get_word_comparison(self, user_input, expected_text):
        """Get detailed word-by-word comparison with specific feedback."""
        if not user_input or not expected_text:
            return {
                'word_analysis': [],
                'missing_words': [],
                'extra_words': [],
                'incorrect_words': []
            }
        
        # Clean and split into words
        user_words = user_input.lower().strip().split()
        expected_words = expected_text.lower().strip().split()
        
        word_analysis = []
        incorrect_words = []
        missing_words = []
        extra_words = []
        
        # Use difflib for better word matching
        import difflib
        matcher = difflib.SequenceMatcher(None, user_words, expected_words)
        
        user_idx = 0
        expected_idx = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Words match exactly
                for k in range(i2 - i1):
                    word_analysis.append({
                        'user_word': user_words[i1 + k],
                        'expected_word': expected_words[j1 + k],
                        'status': 'correct',
                        'position': len(word_analysis)
                    })
            elif tag == 'replace':
                # Words are different
                for k in range(max(i2 - i1, j2 - j1)):
                    user_word = user_words[i1 + k] if i1 + k < i2 else None
                    expected_word = expected_words[j1 + k] if j1 + k < j2 else None
                    
                    if user_word and expected_word:
                        # Check if it's a close match (similar spelling)
                        similarity = difflib.SequenceMatcher(None, user_word, expected_word).ratio()
                        if similarity > 0.6:  # 60% similarity threshold
                            status = 'close'
                        else:
                            status = 'incorrect'
                        
                        word_analysis.append({
                            'user_word': user_word,
                            'expected_word': expected_word,
                            'status': status,
                            'position': len(word_analysis),
                            'similarity': round(similarity * 100)
                        })
                        incorrect_words.append({
                            'user_word': user_word,
                            'expected_word': expected_word,
                            'position': len(word_analysis) - 1
                        })
                    elif expected_word:
                        missing_words.append({
                            'word': expected_word,
                            'position': len(word_analysis)
                        })
                    elif user_word:
                        extra_words.append({
                            'word': user_word,
                            'position': len(word_analysis)
                        })
            elif tag == 'delete':
                # User said extra words
                for k in range(i2 - i1):
                    extra_words.append({
                        'word': user_words[i1 + k],
                        'position': len(word_analysis)
                    })
            elif tag == 'insert':
                # User missed words
                for k in range(j2 - j1):
                    missing_words.append({
                        'word': expected_words[j1 + k],
                        'position': len(word_analysis)
                    })
        
        return {
            'word_analysis': word_analysis,
            'missing_words': missing_words,
            'extra_words': extra_words,
            'incorrect_words': incorrect_words,
            'total_expected_words': len(expected_words),
            'total_user_words': len(user_words),
            'correct_words': len([w for w in word_analysis if w['status'] == 'correct'])
        }

    def post(self, request, room_id=None):
        try:
            room = self.get_room(room_id)
            if not room:
                return JsonResponse({'error': 'Room not found'}, status=404)

            # Get current conversation session
            current_session = room.conversation_sessions.filter(is_completed=False).first()
            
            if not current_session:
                return JsonResponse({'error': 'No active conversation. Please select a topic first.'}, status=400)

            # Handle audio input
            if 'audio' in request.FILES:
                return self._handle_audio_message(request, room, current_session)
            
            # Handle text input
            else:
                return self._handle_text_message(request, room, current_session)
                
        except Exception as e:
            print(f"Error in MessageView: {str(e)}")
            return JsonResponse({'error': 'Failed to process message'}, status=500)

    def _handle_audio_message(self, request, room, session):
        """Handle audio message processing"""
        audio_file = request.FILES['audio']
        
        # Get current exchange
        current_exchange = session.get_current_exchange()
        if not current_exchange:
            return JsonResponse({'error': 'Conversation completed'}, status=400)
        
        expected_response = current_exchange['user_should_say']
        
        # Process audio file
        temp_file = None
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            for chunk in audio_file.chunks():
                temp_file.write(chunk)
            temp_file.close()
            
            # Convert audio to text using Whisper
            transcribed_text = transcribe_audio(temp_file.name)

            # Calculate spelling score and get detailed comparison
            spelling_score = self.calculate_spelling_score(transcribed_text, expected_response)
            word_comparison = self.get_word_comparison(transcribed_text, expected_response)

            # Create user message
            user_message = Message.objects.create(
                room=room,
                role='user',
                content=transcribed_text,
                original_text=transcribed_text,
                conversation_session=session,
                spelling_score=spelling_score
            )
            
            return self._process_user_response(transcribed_text, expected_response, spelling_score, word_comparison, room, session)
            
        finally:
            # Clean up the temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except Exception as e:
                    print(f"Error deleting temporary file: {str(e)}")

    def _handle_text_message(self, request, room, session):
        """Handle text message processing"""
        data = json.loads(request.body)
        user_input = data.get('content', '').strip()
        
        if not user_input:
            return JsonResponse({'error': 'No content provided'}, status=400)

        # Get current exchange
        current_exchange = session.get_current_exchange()
        if not current_exchange:
            return JsonResponse({'error': 'Conversation completed'}, status=400)
        
        expected_response = current_exchange['user_should_say']
        
        # Calculate spelling score and get detailed comparison
        spelling_score = self.calculate_spelling_score(user_input, expected_response)
        word_comparison = self.get_word_comparison(user_input, expected_response)

        # Create user message
        user_message = Message.objects.create(
            room=room,
            role='user',
            content=user_input,
            original_text=user_input,
            conversation_session=session,
            spelling_score=spelling_score
        )
        
        return self._process_user_response(user_input, expected_response, spelling_score, word_comparison, room, session)

    def _process_user_response(self, user_input, expected_response, spelling_score, word_comparison, room, session):
        """Process the user's response and determine next action"""
        
        # Threshold for acceptable pronunciation/spelling
        ACCEPTABLE_SCORE = 70
        
        # Generate feedback message based on word comparison
        def generate_detailed_feedback():
            feedback_parts = []
            
            if word_comparison['correct_words'] > 0:
                feedback_parts.append(f"✅ Correct words: {word_comparison['correct_words']}/{word_comparison['total_expected_words']}")
            
            if word_comparison['incorrect_words']:
                feedback_parts.append("❌ Incorrect words:")
                for wrong in word_comparison['incorrect_words']:
                    feedback_parts.append(f"   • You said '{wrong['user_word']}' but should say '{wrong['expected_word']}'")
            
            if word_comparison['missing_words']:
                missing = [w['word'] for w in word_comparison['missing_words']]
                feedback_parts.append(f"⚠️ Missing words: {', '.join(missing)}")
            
            if word_comparison['extra_words']:
                extra = [w['word'] for w in word_comparison['extra_words']]
                feedback_parts.append(f"➕ Extra words: {', '.join(extra)}")
            
            return "\n".join(feedback_parts) if feedback_parts else "Perfect match!"
        
        if spelling_score >= ACCEPTABLE_SCORE:
            # Good pronunciation - advance to next exchange
            session.advance_to_next_exchange()
            
            if session.is_completed:
                # Conversation completed
                detailed_feedback = generate_detailed_feedback()
                response_content = f"🎯 YOUR RESPONSE: '{user_input}'\n📊 SCORE: {spelling_score}%\n🎯 CORRECT RESPONSE: '{expected_response}'\n\n{detailed_feedback}\n\n🎉 Excellent! You've completed the entire conversation!\n\nClick 'Generate New Conversation' to practice with a different topic."
                
                assistant_message = Message.objects.create(
                    room=room,
                    role='assistant',
                    content=response_content,
                    conversation_session=session
                )
                
                return JsonResponse({
                    'success': True,
                    'conversation_completed': True,
                    'user_message': {
                        'role': 'user',
                        'content': user_input,
                        'spelling_score': spelling_score
                    },
                    'assistant_message': {
                        'role': 'assistant',
                        'content': response_content
                    },
                    'word_comparison': word_comparison,
                    'expected_response': expected_response
                })
            else:
                # Move to next exchange
                next_exchange = session.get_current_exchange()
                detailed_feedback = generate_detailed_feedback()
                
                # Create feedback message
                feedback_content = f"🎯 YOUR RESPONSE: '{user_input}'\n📊 SCORE: {spelling_score}%\n🎯 CORRECT RESPONSE: '{expected_response}'\n\n{detailed_feedback}"
                
                feedback_message = Message.objects.create(
                    room=room,
                    role='assistant',
                    content=feedback_content,
                    conversation_session=session
                )
                
                # Create continuation message
                continuation_content = f"✅ Great! Now let's continue...\n\n{next_exchange['bot_says']}"
                
                continuation_message = Message.objects.create(
                    room=room,
                    role='assistant',
                    content=continuation_content,
                    conversation_session=session,
                    original_text=next_exchange['user_should_say']
                )
                
                return JsonResponse({
                    'success': True,
                    'user_message': {
                        'role': 'user',
                        'content': user_input,
                        'spelling_score': spelling_score
                    },
                    'feedback_message': {
                        'role': 'assistant',
                        'content': feedback_content
                    },
                    'continuation_message': {
                        'role': 'assistant',
                        'content': continuation_content
                    },
                    'expected_response': next_exchange['user_should_say'],
                    'exchange_number': next_exchange['exchange_number'],
                    'total_exchanges': session.dialogue.total_exchanges,
                    'word_comparison': word_comparison,
                    'previous_expected': expected_response
                })
        else:
            # Pronunciation needs improvement - don't advance
            current_exchange = session.get_current_exchange()
            detailed_feedback = generate_detailed_feedback()
            
            response_content = f"🎯 YOUR RESPONSE: '{user_input}'\n📊 SCORE: {spelling_score}%\n🎯 CORRECT RESPONSE: '{expected_response}'\n\n{detailed_feedback}\n\n🔄 Let's try again! Please say: '{expected_response}'\n\n(You need at least 70% accuracy to continue)"
            
            assistant_message = Message.objects.create(
                room=room,
                role='assistant',
                content=response_content,
                conversation_session=session,
                original_text=expected_response
            )
            
            return JsonResponse({
                'success': True,
                'needs_retry': True,
                'user_message': {
                    'role': 'user',
                    'content': user_input,
                    'spelling_score': spelling_score
                },
                'assistant_message': {
                    'role': 'assistant',
                    'content': response_content
                },
                'expected_response': expected_response,
                'exchange_number': current_exchange['exchange_number'],
                'total_exchanges': session.dialogue.total_exchanges,
                'word_comparison': word_comparison
            })

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        
        if not email or not password:
            return render(request, 'login.html', {'error_message': 'Please provide both email and password'})
        
        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                login(request, user)
                return redirect('room')
            else:
                return render(request, 'login.html', {'error_message': 'Invalid email or password'})
        except User.DoesNotExist:
            return render(request, 'login.html', {'error_message': 'Invalid email or password'})
    
    return render(request, 'login.html')

@require_http_methods(["GET", "POST"])
def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        if not all([name, email, password, password_confirm]):
            return render(request, 'signup.html', {'error_message': 'All fields are required'})
        
        if password != password_confirm:
            return render(request, 'signup.html', {'error_message': 'Passwords do not match'})
        
        if User.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error_message': 'Email already exists'})
        
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
            return render(request, 'signup.html', {'error_message': 'An error occurred while creating your account'})
    
    return render(request, 'signup.html')

@require_http_methods(["GET"])
def logout_view(request):
    logout(request)
    return redirect('login')
