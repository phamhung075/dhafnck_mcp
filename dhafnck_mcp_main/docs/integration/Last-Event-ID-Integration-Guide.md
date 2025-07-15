# Last-Event-ID Integration Guide

## 🎯 **Overview**

This guide provides step-by-step instructions for integrating the enhanced EventStore system that fixes Last-Event-ID disconnect/reconnect issues in your existing MCP server.

## 🔍 **Problem Analysis**

Your current MCP server has the following issues with Last-Event-ID handling:

### **❌ Current Issues**
1. **Event ID Format**: Uses `session_id:timestamp:random` instead of proper ordered IDs
2. **Event Storage Order**: Events stored in reverse order (newest first)
3. **Replay Logic**: Uses array indices instead of timestamp comparison
4. **Stream Management**: Missing proper stream-level event management

### **✅ Fixed Implementation**
1. **Proper Event IDs**: Format `stream_id:timestamp_ms:sequence` for ordering
2. **Chronological Storage**: Events stored oldest-first for proper replay
3. **Timestamp-Based Replay**: Uses numeric timestamps for event filtering
4. **Stream-Level Management**: Proper stream and session separation

## 🔧 **Integration Steps**

### **Step 1: Update Session Store** ✅ *COMPLETED*

The enhanced `session_store.py` has been updated with:

```python
# Key improvements in SessionEvent class:
- Added stream_id field for proper stream management
- Added event_id field with unique, ordered IDs
- Added get_numeric_id() method for timestamp extraction
- Fixed event storage order (chronological)
- Enhanced replay_events_after() method
```

### **Step 2: Update Docker Configuration** ✅ *COMPLETED*

Enhanced `docker-compose.redis.yml` with:

```yaml
# New environment variables for Last-Event-ID support:
- ENABLE_EVENT_REPLAY=true
- MAX_EVENTS_PER_SESSION=1000
- EVENT_TTL=3600
- EVENT_COMPRESSION=true
- ENABLE_STREAM_RESUMPTION=true
```

### **Step 3: Redis Configuration** ✅ *COMPLETED*

Optimized `redis.conf` for session storage:

```conf
# Key optimizations:
- appendonly yes (for durability)
- maxmemory-policy allkeys-lru
- notify-keyspace-events Ex
- Sorted set optimizations for event ordering
```

### **Step 4: Testing Infrastructure** ✅ *COMPLETED*

Created comprehensive test script `test-last-event-id.py`:

```python
# Test phases:
1. Initial connection and event reception
2. Simulate disconnect and missed events
3. Reconnect with Last-Event-ID header
4. Verify event ordering and completeness
```

## 🚀 **Deployment Instructions**

### **1. Stop Current Services**

```bash
# Your current command
docker system prune -f && \
docker-compose -f docker/docker-compose.redis.yml down && \
docker-compose -f docker/docker-compose.redis.yml build --no-cache dhafnck-mcp && \
./scripts/manage-docker.sh start
```

### **2. Deploy Enhanced Version**

```bash
# Build with the new EventStore
docker-compose -f docker/docker-compose.redis.yml down
docker-compose -f docker/docker-compose.redis.yml build --no-cache dhafnck-mcp
docker-compose -f docker/docker-compose.redis.yml up -d

# Verify deployment
docker-compose -f docker/docker-compose.redis.yml logs -f dhafnck-mcp
```

### **3. Test Last-Event-ID Functionality**

```bash
# Make the test script executable
chmod +x scripts/test-last-event-id.py

# Run the test
python3 scripts/test-last-event-id.py http://localhost:8080 --verbose

# Expected output:
# 🧪 Starting Last-Event-ID Test
# ✅ Initialized connection
# 📊 Phase 1 complete: X events received
# 💾 Stored last event ID: stream_id:timestamp:sequence
# 🔄 Reconnecting with Last-Event-ID
# ✅ Events are properly ordered by timestamp
# 🎉 Last-Event-ID test completed successfully!
```

## 📊 **Verification Checklist**

### **✅ Basic Functionality**
- [ ] Server starts without errors
- [ ] Redis connection established
- [ ] Memory fallback works when Redis unavailable
- [ ] Health checks pass

### **✅ Last-Event-ID Features**
- [ ] Event IDs follow format: `stream_id:timestamp_ms:sequence`
- [ ] Events stored in chronological order
- [ ] Reconnection with Last-Event-ID header works
- [ ] Missed events are replayed correctly
- [ ] Event ordering maintained during replay

### **✅ Performance**
- [ ] Event storage performance acceptable
- [ ] Memory usage within limits
- [ ] Redis memory usage optimized
- [ ] No memory leaks in fallback mode

## 🔧 **Configuration Options**

### **Environment Variables**

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_EVENT_REPLAY` | `true` | Enable Last-Event-ID replay |
| `MAX_EVENTS_PER_SESSION` | `1000` | Max events per session/stream |
| `EVENT_TTL` | `3600` | Event TTL in seconds |
| `EVENT_COMPRESSION` | `true` | Compress stored events |
| `ENABLE_STREAM_RESUMPTION` | `true` | Enable stream resumption |
| `FALLBACK_TO_MEMORY` | `true` | Use memory when Redis unavailable |

### **Redis Configuration**

```bash
# Key Redis settings in docker-compose.yml:
REDIS_MAX_MEMORY=256mb
REDIS_EVICTION_POLICY=allkeys-lru
REDIS_AOF_ENABLED=yes
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **1. Events Not Replaying**
```bash
# Check event storage
docker exec dhafnck-mcp-redis redis-cli
> KEYS mcp:session:*
> ZRANGE mcp:session:test_session:stream:test_stream 0 -1 WITHSCORES
```

#### **2. Memory Fallback Not Working**
```bash
# Check logs for fallback activation
docker-compose logs dhafnck-mcp | grep "fallback"
# Expected: "Falling back to memory-based session storage"
```

#### **3. Event ID Format Issues**
```bash
# Verify event ID format in logs
docker-compose logs dhafnck-mcp | grep "event_id"
# Expected format: stream_id:1234567890123:000001
```

### **Debug Mode**

```bash
# Enable debug logging
export LOG_LEVEL=debug
export FASTMCP_LOG_LEVEL=DEBUG
docker-compose up dhafnck-mcp
```

## 📈 **Monitoring**

### **Health Checks**

```bash
# Server health
curl http://localhost:8080/health

# Redis health
docker exec dhafnck-mcp-redis redis-cli ping
```

### **Redis Monitoring UI** (Optional)

```bash
# Enable Redis monitoring
export COMPOSE_PROFILES=monitoring
docker-compose up -d redis-commander

# Access UI: http://localhost:8081
```

### **Event Storage Monitoring**

```bash
# Check event counts
redis-cli
> INFO keyspace
> MEMORY usage mcp:session:*
```

## 🔄 **Migration from Old Version**

### **Data Migration** (If Needed)

```python
# Script to migrate old event format to new format
# (Only needed if you have existing session data)

import redis
import json
import time

r = redis.Redis(host='localhost', port=6379)

# Get all old session keys
old_keys = r.keys('mcp:session:*')

for old_key in old_keys:
    # Migrate old list-based storage to sorted set
    old_events = r.lrange(old_key, 0, -1)
    
    for i, event_data in enumerate(old_events):
        event = json.loads(event_data)
        # Update event format and re-store
        # ... migration logic
```

### **Rollback Plan**

```bash
# If issues occur, rollback to previous version
git checkout HEAD~1 -- src/fastmcp/server/session_store.py
docker-compose build --no-cache dhafnck-mcp
docker-compose up -d
```

## 🎯 **Performance Tuning**

### **For High-Traffic Scenarios**

```yaml
# docker-compose.yml adjustments
environment:
  - MAX_EVENTS_PER_SESSION=5000
  - MAX_CONCURRENT_STREAMS=500
  - WORKER_PROCESSES=4
  - REDIS_MAX_MEMORY=1gb
```

### **For Low-Memory Environments**

```yaml
environment:
  - MAX_EVENTS_PER_SESSION=100
  - EVENT_TTL=1800
  - REDIS_MAX_MEMORY=64mb
  - EVENT_COMPRESSION=true
```

## 📚 **Additional Resources**

- [MCP Streamable HTTP Specification](../transports/Streamable%20HTTP.md)
- [Redis Sorted Sets Documentation](https://redis.io/docs/data-types/sorted-sets/)
- [Server-Sent Events Specification](https://html.spec.whatwg.org/multipage/server-sent-events.html)

## 🤝 **Support**

If you encounter issues:

1. **Check Logs**: `docker-compose logs dhafnck-mcp`
2. **Run Tests**: `python3 scripts/test-last-event-id.py`
3. **Verify Configuration**: Check environment variables
4. **Test Redis**: Ensure Redis is accessible and configured correctly

The enhanced EventStore system provides robust Last-Event-ID support while maintaining backward compatibility with your existing MCP server infrastructure. 