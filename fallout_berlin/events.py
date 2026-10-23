"""
Event System
Implements a simple Publisher/Subscriber pattern for decoupling game logic.
"""

from typing import Dict, List, Callable, Any, Optional
from enum import Enum, auto


class EventType(Enum):
    """Enumeration of all possible game event types"""
    LOCATION_ENTER = auto()
    LOCATION_EXIT = auto()
    ITEM_PICKUP = auto()
    ITEM_USE = auto()
    COMBAT_START = auto()
    COMBAT_END = auto()
    QUEST_START = auto()
    QUEST_COMPLETE = auto()
    QUEST_UPDATE = auto()
    LEVEL_UP = auto()
    DIALOGUE_START = auto()
    DIALOGUE_END = auto()
    GAME_TICK = auto() # Periodic event for time/survival updates
    FACTION_REP_CHANGE = auto()
    RADIO_MESSAGE = auto()


class Event:
    """Represents a game event with data"""
    def __init__(self, type: EventType, data: Dict[str, Any] = None):
        self.type = type
        self.data = data or {}


class EventManager:
    """Manages event subscriptions and dispatching"""
    
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable[[Event], None]]] = {}
    
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Subscribe to an event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
    
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]):
        """Unsubscribe from an event type"""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)
    
    def dispatch(self, event: Event):
        """Dispatch an event to all subscribers"""
        if event.type in self._subscribers:
            for callback in self._subscribers[event.type]:
                try:
                    callback(event)
                except Exception as e:
                    print(f"[ERROR] Event handler failed for {event.type}: {e}")
