"""Tests for EventBus implementation."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from typing import List, Any

from fastmcp.task_management.infrastructure.event_bus import EventBus, EventSubscription


def create_named_mock(name: str) -> Mock:
    """Create a Mock with a __name__ attribute for EventBus logging."""
    mock = Mock()
    mock.__name__ = name
    return mock


class TestEventClass:
    """Test event class."""
    def __init__(self, data: str):
        self.data = data


class AnotherTestEventClass:
    """Another test event class."""
    def __init__(self, value: int):
        self.value = value


class TestEventBus:
    """Test suite for EventBus."""
    
    @pytest.fixture
    def event_bus(self):
        """Create an EventBus instance."""
        return EventBus()
    
    def test_initialization(self, event_bus):
        """Test EventBus initialization."""
        assert event_bus._subscriptions == {}
        assert hasattr(event_bus, '_active_handlers')
        assert hasattr(event_bus, '_event_queue')
        assert hasattr(event_bus, '_processing_task')
        assert event_bus._shutdown is False
    
    def test_subscribe_handler(self, event_bus):
        """Test subscribing a handler."""
        handler = create_named_mock("test_handler")
        
        event_bus.subscribe(TestEventClass, handler)
        
        assert TestEventClass in event_bus._subscriptions
        assert len(event_bus._subscriptions[TestEventClass]) == 1
        subscription = event_bus._subscriptions[TestEventClass][0]
        assert subscription.handler == handler
        assert subscription.event_type == TestEventClass
        assert subscription.priority == 0
        assert subscription.is_async is False
    
    def test_subscribe_with_priority(self, event_bus):
        """Test subscribing handlers with different priorities."""
        handler1 = create_named_mock("handler1")
        handler2 = create_named_mock("handler2")
        handler3 = create_named_mock("handler3")
        
        event_bus.subscribe(TestEventClass, handler1, priority=5)
        event_bus.subscribe(TestEventClass, handler2, priority=10)
        event_bus.subscribe(TestEventClass, handler3, priority=1)
        
        subscriptions = event_bus._subscriptions[TestEventClass]
        assert len(subscriptions) == 3
        
        # Should be sorted by priority (descending)
        assert subscriptions[0].handler == handler2  # priority 10
        assert subscriptions[1].handler == handler1  # priority 5
        assert subscriptions[2].handler == handler3  # priority 1
    
    def test_subscribe_async_handler(self, event_bus):
        """Test subscribing an async handler."""
        async def async_handler(event):
            pass
        
        event_bus.subscribe(TestEventClass, async_handler)
        
        subscription = event_bus._subscriptions[TestEventClass][0]
        assert subscription.is_async is True
    
    def test_unsubscribe_handler(self, event_bus):
        """Test unsubscribing a handler."""
        handler = create_named_mock("handler")
        
        event_bus.subscribe(TestEventClass, handler)
        result = event_bus.unsubscribe(TestEventClass, handler)
        
        assert result is True
        assert TestEventClass not in event_bus._subscriptions
    
    def test_unsubscribe_nonexistent_handler(self, event_bus):
        """Test unsubscribing a handler that wasn't subscribed."""
        handler = create_named_mock("handler")
        
        result = event_bus.unsubscribe(TestEventClass, handler)
        
        assert result is False
        assert TestEventClass not in event_bus._subscriptions
    
    def test_unsubscribe_partial(self, event_bus):
        """Test unsubscribing one of multiple handlers."""
        handler1 = create_named_mock("handler1")
        handler2 = create_named_mock("handler2")
        
        event_bus.subscribe(TestEventClass, handler1)
        event_bus.subscribe(TestEventClass, handler2)
        
        result = event_bus.unsubscribe(TestEventClass, handler1)
        
        assert result is True
        assert TestEventClass in event_bus._subscriptions
        assert len(event_bus._subscriptions[TestEventClass]) == 1
        assert event_bus._subscriptions[TestEventClass][0].handler == handler2
    
    @pytest.mark.asyncio
    async def test_publish_to_sync_handler(self, event_bus):
        """Test publishing event to synchronous handler."""
        handler = create_named_mock("handler")
        event = TestEventClass("test_data")
        
        event_bus.subscribe(TestEventClass, handler)
        await event_bus.publish(event)
        
        handler.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_publish_to_async_handler(self, event_bus):
        """Test publishing event to asynchronous handler."""
        handler = AsyncMock()
        event = TestEventClass("test_data")
        
        event_bus.subscribe(TestEventClass, handler)
        await event_bus.publish(event)
        
        handler.assert_awaited_once_with(event)
    
    @pytest.mark.asyncio
    async def test_publish_to_multiple_handlers(self, event_bus):
        """Test publishing event to multiple handlers."""
        handler1 = create_named_mock("handler1")
        handler2 = AsyncMock()
        handler2.__name__ = "handler2"
        handler3 = create_named_mock("handler3")
        event = TestEventClass("test_data")
        
        event_bus.subscribe(TestEventClass, handler1)
        event_bus.subscribe(TestEventClass, handler2)
        event_bus.subscribe(TestEventClass, handler3)
        
        await event_bus.publish(event)
        
        handler1.assert_called_once_with(event)
        handler2.assert_awaited_once_with(event)
        handler3.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_publish_respects_priority_order(self, event_bus):
        """Test that handlers are called in priority order."""
        call_order = []
        
        def make_handler(name):
            def handler(event):
                call_order.append(name)
            return handler
        
        handler1 = make_handler("handler1")
        handler2 = make_handler("handler2")
        handler3 = make_handler("handler3")
        
        event_bus.subscribe(TestEventClass, handler1, priority=5)
        event_bus.subscribe(TestEventClass, handler2, priority=10)  # Highest priority
        event_bus.subscribe(TestEventClass, handler3, priority=1)
        
        event = TestEventClass("test_data")
        await event_bus.publish(event)
        
        # Should be called in descending priority order
        assert call_order == ["handler2", "handler1", "handler3"]
    
    @pytest.mark.asyncio
    async def test_publish_no_handlers(self, event_bus):
        """Test publishing event with no handlers."""
        event = TestEventClass("test_data")
        
        # Should not raise an error
        await event_bus.publish(event)
    
    @pytest.mark.asyncio
    async def test_handler_exception_handling(self, event_bus):
        """Test that handler exceptions don't stop other handlers."""
        handler1 = create_named_mock("handler1")
        handler1.side_effect = Exception("Handler 1 error")
        handler2 = create_named_mock("handler2")
        handler3 = create_named_mock("handler3")
        
        event_bus.subscribe(TestEventClass, handler1)
        event_bus.subscribe(TestEventClass, handler2)
        event_bus.subscribe(TestEventClass, handler3)
        
        event = TestEventClass("test_data")
        
        # Should not raise, but log the error
        with patch('fastmcp.task_management.infrastructure.event_bus.logger') as mock_logger:
            await event_bus.publish(event)
            
            # Other handlers should still be called
            handler2.assert_called_once_with(event)
            handler3.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_publish_different_event_types(self, event_bus):
        """Test publishing different event types."""
        handler1 = create_named_mock("handler1")
        handler2 = create_named_mock("handler2")
        
        event_bus.subscribe(TestEventClass, handler1)
        event_bus.subscribe(AnotherTestEventClass, handler2)
        
        event1 = TestEventClass("test")
        event2 = AnotherTestEventClass(42)
        
        await event_bus.publish(event1)
        await event_bus.publish(event2)
        
        handler1.assert_called_once_with(event1)
        handler2.assert_called_once_with(event2)
    
    def test_get_handlers_for_type(self, event_bus):
        """Test getting handlers for an event type."""
        handler1 = create_named_mock("handler1")
        handler2 = create_named_mock("handler2")
        
        event_bus.subscribe(TestEventClass, handler1)
        event_bus.subscribe(TestEventClass, handler2)
        
        subscriptions = event_bus._subscriptions.get(TestEventClass, [])
        handlers = [sub.handler for sub in subscriptions]
        
        assert handler1 in handlers
        assert handler2 in handlers
    
    def test_get_handlers_empty(self, event_bus):
        """Test getting handlers when none are subscribed."""
        subscriptions = event_bus._subscriptions.get(TestEventClass, [])
        assert subscriptions == []
    
    @pytest.mark.asyncio
    async def test_publish_with_inheritance(self, event_bus):
        """Test that subclass events trigger parent class handlers."""
        class BaseEvent:
            pass
        
        class DerivedEvent(BaseEvent):
            pass
        
        handler = create_named_mock("handler")
        event_bus.subscribe(BaseEvent, handler)
        
        event = DerivedEvent()
        await event_bus.publish(event)
        
        # Handler should be called for derived event due to MRO
        handler.assert_called_once_with(event)
    
    @pytest.mark.asyncio
    async def test_concurrent_publish(self, event_bus):
        """Test concurrent event publishing."""
        handler = create_named_mock("handler")
        event_bus.subscribe(TestEventClass, handler)
        
        events = [TestEventClass(f"event_{i}") for i in range(10)]
        
        # Publish events concurrently
        await asyncio.gather(*[event_bus.publish(event) for event in events])
        
        # Handler should be called for each event
        assert handler.call_count == 10
    
    def test_subscribe_same_handler_multiple_times(self, event_bus):
        """Test subscribing the same handler multiple times."""
        handler = create_named_mock("handler")
        
        event_bus.subscribe(TestEventClass, handler)
        event_bus.subscribe(TestEventClass, handler)  # Subscribe again
        
        # Handler should be in the list twice
        subscriptions = event_bus._subscriptions[TestEventClass]
        handlers = [sub.handler for sub in subscriptions]
        assert handlers.count(handler) == 2
    
    def test_event_subscription_dataclass(self):
        """Test EventSubscription dataclass."""
        handler = create_named_mock("handler")
        subscription = EventSubscription(
            event_type=TestEventClass,
            handler=handler,
            priority=5,
            is_async=False
        )
        
        assert subscription.event_type == TestEventClass
        assert subscription.handler == handler
        assert subscription.priority == 5
        assert subscription.is_async is False


class TestEventBusSingleton:
    """Test singleton functionality."""
    
    @pytest.mark.asyncio
    async def test_get_event_bus_singleton(self):
        """Test that get_event_bus returns the same instance."""
        from fastmcp.task_management.infrastructure.event_bus import get_event_bus
        
        bus1 = get_event_bus()
        bus2 = get_event_bus()
        
        assert bus1 is bus2
    
    @pytest.mark.asyncio
    async def test_reset_event_bus(self):
        """Test resetting the event bus singleton."""
        from fastmcp.task_management.infrastructure.event_bus import get_event_bus, reset_event_bus
        
        bus1 = get_event_bus()
        handler = create_named_mock("handler")
        bus1.subscribe(TestEventClass, handler)
        
        reset_event_bus()
        
        bus2 = get_event_bus()
        assert bus1 is not bus2
        assert TestEventClass not in bus2._subscriptions