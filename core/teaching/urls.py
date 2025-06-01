from django.urls import path
from .views import RoomView, send_message

urlpatterns = [
    path('room/', RoomView.as_view(), name='room'),
    path('room/<int:room_id>/', RoomView.as_view(), name='room_detail'),
    path('room/<int:room_id>/send/', send_message, name='send_message'),
]

