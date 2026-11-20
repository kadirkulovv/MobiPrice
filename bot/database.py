import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Initialize Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# Import Django models after setup
from django.db import close_old_connections
from core.models import (
    Brand, DeviceSeries, DevicePhone, DeviceIssue, IssueComparison,
    RepairFAQ, Review, ServiceOrder, TeamMember, BotAdmin, TelegramUser, AuthToken,
    make_safe_slug
)
from asgiref.sync import sync_to_async

__all__ = [
    'Brand',
    'DeviceSeries',
    'DevicePhone',
    'DeviceIssue',
    'IssueComparison',
    'RepairFAQ',
    'Review',
    'ServiceOrder',
    'TeamMember',
    'BotAdmin',
    'TelegramUser',
    'AuthToken',
    'make_safe_slug',
    'close_old_connections',
    'sync_to_async',
]

