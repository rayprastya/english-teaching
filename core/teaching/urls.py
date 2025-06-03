from django.urls import path
from .views import RoomView, MessageView, login_view, signup_view, logout_view

urlpatterns = [
    path('', RoomView.as_view(), name='room'),  # Main room list view
    path('room/<int:room_id>/', RoomView.as_view(), name='room_detail'),  # Specific room view
    path('room/<int:room_id>/send/', MessageView.as_view(), name='send_message'),
    path('login/', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
]

