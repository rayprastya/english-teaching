from django.urls import path
from .views import RoomView, MessageView

urlpatterns = [
    path('room/', RoomView.as_view(), name='room'),
    path('room/<int:room_id>/', RoomView.as_view(), name='room_detail'),
    path('room/<int:room_id>/send/', MessageView.as_view(), name='send_message'),
]

