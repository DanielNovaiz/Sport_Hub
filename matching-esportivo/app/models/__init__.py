"""Modelos SQLModel do projeto"""

from app.models.club import Club, ClubMember, TeamSynergy
from app.models.event import Event, EventParticipant, Match
from app.models.ranked import UserRank
from app.models.season import Season, SeasonRank, SeasonMilestone, SeasonRewardGrant
from app.models.chat import ChatRoom, ChatMessage
from app.models.court import Court, Booking
from app.models.athlete import Athlete
from app.models.notification import Notification
from app.models.player_stats import MatchPerformance, PlayerStats, UserAchievement, UserPrestige, UserXP
from app.models.user import User, UserInterest

__all__ = [
	"Club",
	"ClubMember",
	"TeamSynergy",
	"Event",
	"Match",
	"EventParticipant",
	"UserRank",
	"Season",
	"SeasonRank",
	"SeasonMilestone",
	"SeasonRewardGrant",
	"ChatRoom",
	"ChatMessage",
	"Court",
	"Booking",
	"Athlete",
	"Notification",
	"PlayerStats",
	"UserXP",
	"UserAchievement",
	"UserPrestige",
	"MatchPerformance",
	"User",
	"UserInterest",
]
