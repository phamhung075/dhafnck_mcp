import express from 'express';
import { EventStoreFactory, EventStoreFactoryConfig } from '../infrastructure/eventstore/EventStoreFactory';
import { StreamHandler, StreamHandlerConfig } from '../infrastructure/http/StreamHandler';

/**
 * Example MCP Server with Hybrid EventStore Integration
 */
class MCPServerWithEventStore {
  private app: express.Application;
  private streamHandler: StreamHandler;

  constructor() {
    this.app = express();
    this.setupMiddleware();
  }

  private setupMiddleware(): void {
    this.app.use(express.json());
    this.app.use(express.urlencoded({ extended: true }));
    
    // CORS headers for MCP
    this.app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Content-Type, Last-Event-ID, MCP-Protocol-Version, Mcp-Session-Id');
      
      if (req.method === 'OPTIONS') {
        res.sendStatus(200);
        return;
      }
      next();
    });
  }

  async initialize(): Promise<void> {
    // Initialize EventStore with hybrid configuration
    const eventStoreConfig: EventStoreFactoryConfig = {
      maxEventsPerStream: parseInt(process.env.MAX_EVENTS_PER_STREAM || '1000'),
      eventTTL: parseInt(process.env.EVENT_TTL || '3600'),
      enableEventReplay: process.env.ENABLE_EVENT_REPLAY === 'true',
      cleanupInterval: parseInt(process.env.CLEANUP_INTERVAL || '300'),
      redisUrl: process.env.REDIS_URL,
      preferRedis: process.env.PREFER_REDIS === 'true',
      fallbackToMemory: process.env.FALLBACK_TO_MEMORY === 'true',
      healthCheckInterval: parseInt(process.env.HEALTH_CHECK_INTERVAL || '30')
    };

    try {
      await EventStoreFactory.createEventStore(eventStoreConfig);
      console.log('✅ EventStore initialized successfully');
    } catch (error) {
      console.error('❌ Failed to initialize EventStore:', error);
      throw error;
    }

    // Initialize StreamHandler
    const streamConfig: StreamHandlerConfig = {
      enableEventReplay: eventStoreConfig.enableEventReplay,
      maxConcurrentStreams: parseInt(process.env.MAX_CONCURRENT_STREAMS || '100'),
      streamTimeoutMs: parseInt(process.env.STREAM_TIMEOUT_MS || '300000')
    };

    this.streamHandler = new StreamHandler(streamConfig);
    
    this.setupRoutes();
  }

  private setupRoutes(): void {
    // MCP Endpoint - Handle both POST and GET
    this.app.all('/mcp', this.handleMCPEndpoint.bind(this));
    
    // Health check endpoint
    this.app.get('/health', this.handleHealthCheck.bind(this));
    
    // Status endpoint for monitoring
    this.app.get('/status', this.handleStatus.bind(this));
  }

  private async handleMCPEndpoint(req: express.Request, res: express.Response): Promise<void> {
    const sessionId = req.headers['mcp-session-id'] as string || this.generateSessionId();
    const lastEventId = req.headers['last-event-id'] as string;
    
    if (req.method === 'GET') {
      // Handle SSE stream request
      const streamId = `stream_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      
      try {
        await this.streamHandler.handleSSEStream(res, sessionId, streamId, lastEventId);
        
        // Example: Send periodic events (in real implementation, this would be driven by actual MCP events)
        this.sendPeriodicEvents(res, sessionId, streamId);
        
      } catch (error) {
        console.error('Failed to handle SSE stream:', error);
        res.status(500).json({ error: 'Failed to establish stream' });
      }
      
    } else if (req.method === 'POST') {
      // Handle JSON-RPC request
      try {
        const mcpRequest = req.body;
        
        // Process the MCP request (simplified example)
        const response = await this.processMCPRequest(mcpRequest, sessionId);
        
        // Check if client accepts SSE
        const acceptsSSE = req.headers.accept?.includes('text/event-stream');
        
        if (acceptsSSE) {
          // Return SSE stream with response
          const streamId = `stream_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
          await this.streamHandler.handleSSEStream(res, sessionId, streamId, lastEventId);
          
          // Send the response as an SSE event
          await this.streamHandler.sendSSEEvent(res, {
            id: this.generateEventId(),
            sessionId,
            streamId,
            timestamp: Date.now(),
            data: response,
            type: 'response'
          });
          
          res.end();
        } else {
          // Return JSON response
          res.json(response);
        }
        
      } catch (error) {
        console.error('Failed to process MCP request:', error);
        res.status(400).json({ error: 'Failed to process request' });
      }
    }
  }

  private async processMCPRequest(request: any, sessionId: string): Promise<any> {
    // Simplified MCP request processing
    // In real implementation, this would handle various MCP methods
    
    switch (request.method) {
      case 'initialize':
        return {
          jsonrpc: '2.0',
          id: request.id,
          result: {
            protocolVersion: '2025-06-18',
            capabilities: {
              logging: {},
              prompts: { listChanged: true },
              resources: { subscribe: true, listChanged: true },
              tools: { listChanged: true }
            },
            serverInfo: {
              name: 'dhafnck-mcp-server',
              version: '1.0.0'
            }
          }
        };
        
      case 'ping':
        return {
          jsonrpc: '2.0',
          id: request.id,
          result: {}
        };
        
      default:
        throw new Error(`Unknown method: ${request.method}`);
    }
  }

  private async sendPeriodicEvents(res: express.Response, sessionId: string, streamId: string): Promise<void> {
    // Example: Send periodic heartbeat events
    let eventCount = 0;
    const interval = setInterval(async () => {
      try {
        await this.streamHandler.sendSSEEvent(res, {
          id: this.generateEventId(),
          sessionId,
          streamId,
          timestamp: Date.now(),
          data: { 
            type: 'heartbeat', 
            count: ++eventCount,
            timestamp: new Date().toISOString()
          },
          type: 'notification'
        });
        
        // Stop after 10 heartbeats (for demo purposes)
        if (eventCount >= 10) {
          clearInterval(interval);
          res.end();
        }
      } catch (error) {
        console.error('Failed to send periodic event:', error);
        clearInterval(interval);
      }
    }, 5000); // Every 5 seconds
  }

  private async handleHealthCheck(req: express.Request, res: express.Response): Promise<void> {
    try {
      const eventStore = EventStoreFactory.getInstance();
      const isHealthy = eventStore ? await eventStore.isHealthy() : false;
      
      const health = {
        status: isHealthy ? 'healthy' : 'unhealthy',
        timestamp: new Date().toISOString(),
        eventStore: {
          type: eventStore?.getStorageType() || 'none',
          healthy: isHealthy
        },
        streams: this.streamHandler.getStreamStats()
      };
      
      res.status(isHealthy ? 200 : 503).json(health);
    } catch (error) {
      res.status(503).json({
        status: 'error',
        error: (error as Error).message,
        timestamp: new Date().toISOString()
      });
    }
  }

  private async handleStatus(req: express.Request, res: express.Response): Promise<void> {
    try {
      const eventStore = EventStoreFactory.getInstance();
      const factoryStatus = EventStoreFactory.getStatus();
      const streamStats = this.streamHandler.getStreamStats();
      
      const status = {
        server: {
          uptime: process.uptime(),
          memory: process.memoryUsage(),
          timestamp: new Date().toISOString()
        },
        eventStore: factoryStatus,
        streams: streamStats
      };
      
      res.json(status);
    } catch (error) {
      res.status(500).json({
        error: 'Failed to get status',
        message: (error as Error).message
      });
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private generateEventId(): string {
    return `evt_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  async start(port: number = 8080): Promise<void> {
    await this.initialize();
    
    this.app.listen(port, () => {
      console.log(`🚀 MCP Server with EventStore running on port ${port}`);
      console.log(`📊 Health check: http://localhost:${port}/health`);
      console.log(`📈 Status: http://localhost:${port}/status`);
      console.log(`🔌 MCP Endpoint: http://localhost:${port}/mcp`);
    });
  }

  async stop(): Promise<void> {
    this.streamHandler.destroy();
    await EventStoreFactory.destroy();
    console.log('🛑 MCP Server stopped');
  }
}

// Usage example
if (require.main === module) {
  const server = new MCPServerWithEventStore();
  
  server.start().catch(error => {
    console.error('Failed to start server:', error);
    process.exit(1);
  });
  
  // Graceful shutdown
  process.on('SIGINT', async () => {
    console.log('Received SIGINT, shutting down gracefully...');
    await server.stop();
    process.exit(0);
  });
  
  process.on('SIGTERM', async () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    await server.stop();
    process.exit(0);
  });
}

export { MCPServerWithEventStore };
