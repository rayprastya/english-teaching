from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Room, Message
from core.utils.whisper import score_spelling
import json

class RoomView(LoginRequiredMixin, View):
    template_name = 'teaching/room.html'

    def get(self, request, room_id=None):
        if room_id:
            room = get_object_or_404(
                Room.objects.select_related('user'),
                id=room_id,
                user=request.user
            )
            # Get last 50 messages ordered by creation time
            messages = room.messages.all().order_by('-created_at')[:100]
        else:
            room = Room.objects.create(user=request.user)
            return redirect('room', room_id=room.id)

        context = {
            'room': room,
            'messages': messages,
        }
        return render(request, self.template_name, context)
    
    def post(self, request:

class MessageView(LoginRequiredMixin, View):
    """
    Class-based view for handling message operations.
    Handles both sending messages and processing speech input.
    """
    
    def get_room(self, room_id):
        """Helper method to get room with proper permissions"""
        return get_object_or_404(Room, id=room_id, user=self.request.user)

    def process_speech(self, audio_data, expected_text=None):
        """Helper method to process speech input"""
        transcribed, score = score_spelling(audio_data, expected_text)
        return transcribed, score

    def create_message(self, room, content, role, spelling_score=None, original_text=None):
        """Helper method to create a message"""
        return Message.objects.create(
            room=room,
            content=content,
            role=role,
            spelling_score=spelling_score,
            original_text=original_text
        )

    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, room_id):
        room = self.get_room(room_id)
        data = json.loads(request.body)
        
        # Create user message
        user_message = self.create_message(
            room=room,
            content=data.get('message', ''),
            role='user'
        )

        # Process speech if available
        if data.get('audio_data'):
            transcribed, score = self.process_speech(
                data['audio_data'],
                data.get('expected_text', '')
            )
            user_message.spelling_score = score
            user_message.original_text = transcribed
            user_message.save()

        # Create assistant response
        assistant_message = self.create_message(
            room=room,
            content="I'm your English learning assistant. How can I help you today?",
            role='assistant'
        )

        return JsonResponse({
            'user_message': {
                'content': user_message.content,
                'spelling_score': user_message.spelling_score,
                'original_text': user_message.original_text
            },
            'assistant_message': {
                'content': assistant_message.content
            }
        })
