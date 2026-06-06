"""
Backend Endpoints para Sprint 2: Booking Minimalista
Implementação de endpoints para criação e listagem de matches.

Este arquivo fornece exemplos de implementação para FastAPI e Django REST Framework.
"""

# ==================== FASTAPI IMPLEMENTATION ====================

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uuid

router = APIRouter(prefix="/matches", tags=["matches"])


# ==================== MODELS ====================

class MatchCreate(BaseModel):
    court_id: str
    court_name: str
    scheduled_at: datetime


class MatchResponse(BaseModel):
    id: str
    court_id: str
    user_id: str
    court_name: str
    scheduled_at: datetime
    status: str  # "scheduled" ou "cancelled"
    created_at: datetime
    updated_at: Optional[datetime] = None
    version: int


# ==================== ENDPOINTS ====================

@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
async def create_match(
    match_data: MatchCreate,
    user_id: str = Depends(get_current_user_id)  # Função de autenticação
):
    """
    Cria um novo match (booking).
    
    POST /matches
    Body: {
        "court_id": "court123",
        "court_name": "Quadra Central",
        "scheduled_at": "2026-04-28T14:00:00Z"
    }
    """
    # Validações
    if match_data.scheduled_at < datetime.now():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível agendar no passado"
        )
    
    # Verificar disponibilidade da quadra (mock)
    # Em produção, verificar se a quadra está disponível no horário
    
    # Criar match
    new_match = MatchResponse(
        id=str(uuid.uuid4()),
        court_id=match_data.court_id,
        user_id=user_id,
        court_name=match_data.court_name,
        scheduled_at=match_data.scheduled_at,
        status="scheduled",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        version=1
    )
    
    # Salvar no banco de dados
    # db.add(new_match)
    # db.commit()
    
    return new_match


@router.get("/me", response_model=List[MatchResponse])
async def get_user_matches(
    user_id: str = Depends(get_current_user_id)
):
    """
    Lista todos os matches do usuário autenticado.
    
    GET /matches/me
    Retorna lista de matches agendados pelo usuário
    """
    # Buscar matches do usuário no banco de dados
    # matches = db.query(Match).filter(Match.user_id == user_id).all()
    
    # Mock response
    matches = [
        {
            "id": "match123",
            "court_id": "court456",
            "user_id": user_id,
            "court_name": "Quadra Central",
            "scheduled_at": "2026-04-28T14:00:00Z",
            "status": "scheduled",
            "created_at": "2026-04-27T10:00:00Z",
            "updated_at": "2026-04-27T10:00:00Z",
            "version": 1
        }
    ]
    
    return matches


@router.patch("/{match_id}", response_model=MatchResponse)
async def update_match_status(
    match_id: str,
    status_data: dict,
    user_id: str = Depends(get_current_user_id)
):
    """
    Atualiza o status de um match (ex: cancelar).
    
    PATCH /matches/{match_id}
    Body: {
        "status": "cancelled"
    }
    """
    # Buscar match no banco
    # match = db.query(Match).filter(Match.id == match_id).first()
    
    # Verificar se o match pertence ao usuário
    # if match.user_id != user_id:
    #     raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Atualizar status
    # match.status = status_data["status"]
    # match.updated_at = datetime.now()
    # match.version += 1
    # db.commit()
    
    # Mock response
    updated_match = {
        "id": match_id,
        "court_id": "court456",
        "user_id": user_id,
        "court_name": "Quadra Central",
        "scheduled_at": "2026-04-28T14:00:00Z",
        "status": status_data["status"],
        "created_at": "2026-04-27T10:00:00Z",
        "updated_at": datetime.now(),
        "version": 2
    }
    
    return updated_match


# ==================== DJANGO REST FRAMEWORK IMPLEMENTATION ====================

# views.py
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import MatchSerializer, MatchCreateSerializer
from .models import Match

class MatchViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MatchSerializer
    
    def get_queryset(self):
        return Match.objects.filter(user=self.request.user)
    
    def create(self, request):
        serializer = MatchCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Criar match
        match = Match.objects.create(
            user=request.user,
            court_id=serializer.validated_data['court_id'],
            court_name=serializer.validated_data['court_name'],
            scheduled_at=serializer.validated_data['scheduled_at'],
            status='scheduled'
        )
        
        serializer = MatchSerializer(match)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        matches = self.get_queryset()
        serializer = self.get_serializer(matches, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        match = self.get_object()
        
        if match.user != request.user:
            return Response(
                {'error': 'Acesso negado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        match.status = 'cancelled'
        match.version += 1
        match.save()
        
        serializer = self.get_serializer(match)
        return Response(serializer.data)
"""

# urls.py
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchViewSet

router = DefaultRouter()
router.register(r'matches', MatchViewSet, basename='match')

urlpatterns = [
    path('api/v1/', include(router.urls)),
]
"""

# serializers.py
"""
from rest_framework import serializers
from .models import Match

class MatchCreateSerializer(serializers.Serializer):
    court_id = serializers.CharField()
    court_name = serializers.CharField()
    scheduled_at = serializers.DateTimeField()

class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = ['id', 'court_id', 'user_id', 'court_name', 'scheduled_at', 
                  'status', 'created_at', 'updated_at', 'version']
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at', 'version']
"""

# models.py
"""
from django.db import models
from django.contrib.auth.models import User

class Match(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    court_id = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    court_name = models.CharField(max_length=200)
    scheduled_at = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    version = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-scheduled_at']
