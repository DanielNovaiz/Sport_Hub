"""
Backend Endpoints para Sprint 3: Notificações e Chat
Implementação de endpoints para notificações e mensagens entre jogadores.

Este arquivo fornece exemplos de implementação para FastAPI e Django REST Framework.
"""

# ==================== FASTAPI IMPLEMENTATION ====================

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/notifications", tags=["notifications"])


# ==================== NOTIFICATION MODELS ====================

class NotificationType(str):
    MATCH_CREATED = "match_created"
    MATCH_CANCELLED = "match_cancelled"
    MATCH_REMINDER = "match_reminder"
    NEW_MESSAGE = "new_message"
    PLAYER_JOINED = "player_joined"
    PLAYER_LEFT = "player_left"


class NotificationCreate(BaseModel):
    user_id: str
    type: NotificationType
    title: str
    body: str
    match_id: Optional[str] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: NotificationType
    title: str
    body: str
    match_id: Optional[str] = None
    sender_id: Optional[str] = None
    sender_name: Optional[str] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None


# ==================== NOTIFICATION ENDPOINTS ====================

@router.post("/", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
async def create_notification(
    notification_data: NotificationCreate,
    user_id: str = Depends(get_current_user_id)  # Função de autenticação
):
    """
    Cria uma nova notificação.
    
    POST /notifications
    Body: {
        "user_id": "user123",
        "type": "match_created",
        "title": "Novo match agendado",
        "body": "Você agendou um match na Quadra Central",
        "match_id": "match123"
    }
    """
    new_notification = NotificationResponse(
        id=str(uuid.uuid4()),
        user_id=notification_data.user_id,
        type=notification_data.type,
        title=notification_data.title,
        body=notification_data.body,
        match_id=notification_data.match_id,
        sender_id=notification_data.sender_id,
        sender_name=notification_data.sender_name,
        is_read=False,
        created_at=datetime.now(),
    )
    
    # Salvar no banco de dados
    # db.add(new_notification)
    # db.commit()
    
    return new_notification


@router.get("/me", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista todas as notificações do usuário autenticado.
    
    GET /notifications/me
    Retorna lista de notificações do usuário
    """
    # Buscar notificações do usuário no banco de dados
    # notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
    
    # Mock response
    notifications = [
        {
            "id": "notif1",
            "user_id": user_id,
            "type": "match_created",
            "title": "Novo match agendado",
            "body": "Você agendou um match na Quadra Central",
            "match_id": "match123",
            "sender_id": None,
            "sender_name": None,
            "is_read": False,
            "created_at": "2026-04-27T10:00:00Z",
            "read_at": None,
        }
    ]
    
    return notifications


@router.patch("/{notification_id}", response_model=NotificationResponse)
async def update_notification(
    notification_id: str,
    update_data: dict,
    user_id: str = Depends(get_current_user_id)
):
    """
    Atualiza uma notificação (ex: marcar como lida).
    
    PATCH /notifications/{notification_id}
    Body: {
        "is_read": true,
        "read_at": "2026-04-27T10:30:00Z"
    }
    """
    # Buscar notificação no banco
    # notification = db.query(Notification).filter(Notification.id == notification_id).first()
    
    # Verificar se a notificação pertence ao usuário
    # if notification.user_id != user_id:
    #     raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Atualizar notificação
    # notification.is_read = update_data.get("is_read", notification.is_read)
    # notification.read_at = update_data.get("read_at")
    # db.commit()
    
    # Mock response
    updated_notification = {
        "id": notification_id,
        "user_id": user_id,
        "type": "match_created",
        "title": "Novo match agendado",
        "body": "Você agendou um match na Quadra Central",
        "match_id": "match123",
        "sender_id": None,
        "sender_name": None,
        "is_read": update_data.get("is_read", False),
        "created_at": "2026-04-27T10:00:00Z",
        "read_at": update_data.get("read_at"),
    }
    
    return updated_notification


@router.patch("/me/mark-all-read")
async def mark_all_as_read(
    user_id: str = Depends(get_current_user_id)
):
    """
    Marca todas as notificações do usuário como lidas.
    
    PATCH /notifications/me/mark-all-read
    """
    # Atualizar todas as notificações não lidas do usuário
    # db.query(Notification).filter(
    #     Notification.user_id == user_id,
    #     Notification.is_read == False
    # ).update({"is_read": True, "read_at": datetime.now()})
    # db.commit()
    
    return {"message": "Todas as notificações marcadas como lidas"}


# ==================== MESSAGE MODELS ====================

class MessageCreate(BaseModel):
    match_id: str
    content: str
    sender_name: str


class MessageResponse(BaseModel):
    id: str
    match_id: str
    sender_id: str
    sender_name: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    version: int


# ==================== MESSAGE ENDPOINTS ====================

message_router = APIRouter(prefix="/messages", tags=["messages"])


@message_router.post("/", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    message_data: MessageCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Cria uma nova mensagem em um chat de match.
    
    POST /messages
    Body: {
        "match_id": "match123",
        "content": "Olá, vamos jogar?",
        "sender_name": "João"
    }
    """
    new_message = MessageResponse(
        id=str(uuid.uuid4()),
        match_id=message_data.match_id,
        sender_id=user_id,
        sender_name=message_data.sender_name,
        content=message_data.content,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1,
    )
    
    # Salvar no banco de dados
    # db.add(new_message)
    # db.commit()
    
    return new_message


@message_router.get("/{match_id}", response_model=List[MessageResponse])
async def get_match_messages(
    match_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista todas as mensagens de um match.
    
    GET /messages/{match_id}
    Retorna lista de mensagens do chat do match
    """
    # Buscar mensagens do match no banco de dados
    # messages = db.query(Message).filter(Message.match_id == match_id).all()
    
    # Mock response
    messages = [
        {
            "id": "msg1",
            "match_id": match_id,
            "sender_id": "user1",
            "sender_name": "João",
            "content": "Olá, vamos jogar?",
            "created_at": "2026-04-27T10:00:00Z",
            "updated_at": "2026-04-27T10:00:00Z",
            "version": 1,
        }
    ]
    
    return messages


# ==================== DJANGO REST FRAMEWORK IMPLEMENTATION ====================

# views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import NotificationSerializer, MessageSerializer
from .models import Notification, Message

class NotificationViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def create(self, request):
        serializer = NotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        notification = Notification.objects.create(
            user=request.user,
            **serializer.validated_data
        )
        
        serializer = NotificationSerializer(notification)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        notifications = self.get_queryset()
        serializer = self.get_serializer(notifications, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        
        if notification.user != request.user:
            return Response(
                {'error': 'Acesso negado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def mark_all_read(self, request):
        Notification.objects.filter(
            user=request.user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
        
        return Response({'message': 'Todas as notificações marcadas como lidas'})


class MessageViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer
    
    def get_queryset(self):
        match_id = self.kwargs.get('match_id')
        if match_id:
            return Message.objects.filter(match_id=match_id)
        return Message.objects.none()
    
    def create(self, request):
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = Message.objects.create(
            sender=request.user,
            **serializer.validated_data
        )
        
        serializer = MessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def by_match(self, request, match_id):
        messages = Message.objects.filter(match_id=match_id)
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
"""

# urls.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
"""

# serializers.py
"""
from rest_framework import serializers
from .models import Notification, Message

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'user_id', 'type', 'title', 'body', 'match_id', 
                  'sender_id', 'sender_name', 'is_read', 'created_at', 'read_at']
        read_only_fields = ['id', 'created_at', 'read_at']

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'match_id', 'sender_id', 'sender_name', 'content', 
                  'created_at', 'updated_at', 'version']
        read_only_fields = ['id', 'sender_id', 'created_at', 'updated_at', 'version']
"""

# models.py
"""
from django.db import models
from django.contrib.auth.models import User

class Notification(models.Model):
    TYPE_CHOICES = [
        ('match_created', 'Match Created'),
        ('match_cancelled', 'Match Cancelled'),
        ('match_reminder', 'Match Reminder'),
        ('new_message', 'New Message'),
        ('player_joined', 'Player Joined'),
        ('player_left', 'Player Left'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField()
    match_id = models.CharField(max_length=100, null=True, blank=True)
    sender_id = models.CharField(max_length=100, null=True, blank=True)
    sender_name = models.CharField(max_length=200, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    match_id = models.CharField(max_length=100)
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    sender_name = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
