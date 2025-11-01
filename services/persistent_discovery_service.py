"""
Persistent Discovery Service Implementation

Provides durable worker registration that survives platform restarts.
Supports multiple backends: Redis, Database, Azure Storage, File-based.
"""

import json
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import asyncio

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

try:
    import aiosqlite
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

from platform_service import WorkerInfo, DiscoveryServiceInterface

logger = logging.getLogger(__name__)

class PersistentDiscoveryService(DiscoveryServiceInterface):
    """Production-ready persistent discovery service with multiple backend options."""
    
    def __init__(self):
        self.backend_type = self._determine_backend()
        self.backend = None
        logger.info(f"🗄️  Initializing persistent discovery with {self.backend_type} backend")
    
    def _determine_backend(self) -> str:
        """Determine which persistence backend to use based on environment and availability."""
        
        # Check environment preference
        preferred = os.getenv("DISCOVERY_BACKEND", "").lower()
        
        # Always prefer external volume-based storage for true persistence
        volume_path = os.getenv("WORKER_REGISTRY_VOLUME", "/data/workers")
        if os.path.exists(os.path.dirname(volume_path)) or preferred == "volume":
            return "volume"
        
        if preferred == "redis" and REDIS_AVAILABLE:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
            return "redis"
        
        # Fallback to enhanced in-memory with worker heartbeat recovery
        logger.warning("⚠️  No persistent storage available, using enhanced in-memory with worker recovery")
        return "memory_enhanced"
    
    async def initialize(self):
        """Initialize the chosen backend."""
        if self.backend_type == "volume":
            await self._initialize_volume()
        elif self.backend_type == "redis":
            await self._initialize_redis()
        elif self.backend_type == "memory_enhanced":
            await self._initialize_memory_enhanced()
        else:
            raise ValueError(f"Unknown backend type: {self.backend_type}")
        
        logger.info(f"✅ Persistent discovery service initialized with {self.backend_type} backend")
    
    async def _initialize_redis(self):
        """Initialize Redis backend."""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.backend = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        try:
            await self.backend.ping()
            logger.info(f"🔌 Connected to Redis at {redis_url}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
    
    async def _initialize_sqlite(self):
        """Initialize SQLite backend."""
        db_path = os.getenv("SQLITE_DB_PATH", "/app/data/workers.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.backend = await aiosqlite.connect(db_path)
        
        # Create workers table
        await self.backend.execute("""
            CREATE TABLE IF NOT EXISTS workers (
                service_type TEXT,
                worker_id TEXT,
                endpoint TEXT,
                capabilities TEXT,
                last_seen TEXT,
                load_score REAL,
                metadata TEXT,
                PRIMARY KEY (service_type, worker_id)
            )
        """)
        await self.backend.commit()
        
        logger.info(f"📁 SQLite database initialized at {db_path}")
    
    async def _initialize_file(self):
        """Initialize file-based backend."""
        self.backend = {
            "data_dir": os.getenv("WORKER_DATA_DIR", "/app/data"),
            "workers_file": "workers.json"
        }
        
        os.makedirs(self.backend["data_dir"], exist_ok=True)
        
        # Load existing data
        workers_path = os.path.join(self.backend["data_dir"], self.backend["workers_file"])
        if os.path.exists(workers_path):
            try:
                with open(workers_path, 'r') as f:
                    self.workers = json.load(f)
                logger.info(f"📂 Loaded existing workers from {workers_path}")
            except Exception as e:
                logger.warning(f"⚠️  Failed to load workers file: {e}, starting fresh")
                self.workers = {}
        else:
            self.workers = {}
        
        logger.info(f"💾 File-based storage initialized at {workers_path}")
    
    async def register_worker(self, worker_info: WorkerInfo) -> bool:
        """Register worker with persistent storage."""
        try:
            if self.backend_type == "redis":
                return await self._register_worker_redis(worker_info)
            elif self.backend_type == "sqlite":
                return await self._register_worker_sqlite(worker_info)
            elif self.backend_type == "file":
                return await self._register_worker_file(worker_info)
            else:
                raise ValueError(f"Unknown backend type: {self.backend_type}")
        except Exception as e:
            logger.error(f"❌ Failed to register worker {worker_info.worker_id}: {e}")
            return False
    
    async def _register_worker_redis(self, worker_info: WorkerInfo) -> bool:
        """Register worker in Redis with TTL."""
        pipe = self.backend.pipeline()
        
        # Store worker data with TTL (5 minutes)
        worker_key = f"worker:{worker_info.service_type}:{worker_info.worker_id}"
        worker_data = asdict(worker_info)
        worker_data['last_seen'] = worker_info.last_seen.isoformat()
        
        pipe.hset(worker_key, mapping=worker_data)
        pipe.expire(worker_key, 300)  # 5 minute TTL
        
        # Add to service type index
        service_key = f"service:{worker_info.service_type}"
        pipe.sadd(service_key, worker_info.worker_id)
        pipe.expire(service_key, 600)  # 10 minute TTL for service index
        
        await pipe.execute()
        
        logger.debug(f"✅ Registered worker {worker_info.worker_id} in Redis")
        return True
    
    async def _register_worker_sqlite(self, worker_info: WorkerInfo) -> bool:
        """Register worker in SQLite database."""
        await self.backend.execute("""
            INSERT OR REPLACE INTO workers 
            (service_type, worker_id, endpoint, capabilities, last_seen, load_score, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            worker_info.service_type,
            worker_info.worker_id,
            worker_info.endpoint,
            json.dumps(worker_info.capabilities),
            worker_info.last_seen.isoformat(),
            worker_info.load_score,
            json.dumps(worker_info.metadata)
        ))
        await self.backend.commit()
        
        logger.debug(f"✅ Registered worker {worker_info.worker_id} in SQLite")
        return True
    
    async def _register_worker_file(self, worker_info: WorkerInfo) -> bool:
        """Register worker in file-based storage."""
        service_type = worker_info.service_type
        
        if service_type not in self.workers:
            self.workers[service_type] = []
        
        # Remove existing worker with same ID
        self.workers[service_type] = [
            w for w in self.workers[service_type] 
            if w.get('worker_id') != worker_info.worker_id
        ]
        
        # Add new worker
        worker_data = asdict(worker_info)
        worker_data['last_seen'] = worker_info.last_seen.isoformat()
        self.workers[service_type].append(worker_data)
        
        # Save to file
        await self._save_workers_file()
        
        logger.debug(f"✅ Registered worker {worker_info.worker_id} in file storage")
        return True
    
    async def _save_workers_file(self):
        """Save workers data to file."""
        workers_path = os.path.join(self.backend["data_dir"], self.backend["workers_file"])
        temp_path = workers_path + ".tmp"
        
        with open(temp_path, 'w') as f:
            json.dump(self.workers, f, indent=2)
        
        # Atomic rename
        os.rename(temp_path, workers_path)
    
    async def find_worker(self, service_type: str) -> Optional[WorkerInfo]:
        """Find best available worker for service type."""
        try:
            if self.backend_type == "redis":
                return await self._find_worker_redis(service_type)
            elif self.backend_type == "sqlite":
                return await self._find_worker_sqlite(service_type)
            elif self.backend_type == "file":
                return await self._find_worker_file(service_type)
            else:
                raise ValueError(f"Unknown backend type: {self.backend_type}")
        except Exception as e:
            logger.error(f"❌ Failed to find worker for {service_type}: {e}")
            return None
    
    async def _find_worker_redis(self, service_type: str) -> Optional[WorkerInfo]:
        """Find worker in Redis."""
        service_key = f"service:{service_type}"
        worker_ids = await self.backend.smembers(service_key)
        
        if not worker_ids:
            return None
        
        # Get all workers and find the least loaded
        workers = []
        for worker_id in worker_ids:
            worker_key = f"worker:{service_type}:{worker_id}"
            worker_data = await self.backend.hgetall(worker_key)
            
            if worker_data:
                # Convert back to WorkerInfo
                worker_data['last_seen'] = datetime.fromisoformat(worker_data['last_seen'])
                worker_data['capabilities'] = json.loads(worker_data.get('capabilities', '[]'))
                worker_data['metadata'] = json.loads(worker_data.get('metadata', '{}'))
                worker_data['load_score'] = float(worker_data.get('load_score', 0.0))
                
                workers.append(WorkerInfo(**worker_data))
        
        if not workers:
            return None
        
        # Return least loaded worker
        return min(workers, key=lambda w: w.load_score)
    
    async def _find_worker_sqlite(self, service_type: str) -> Optional[WorkerInfo]:
        """Find worker in SQLite."""
        # Clean up stale workers (older than 5 minutes)
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        await self.backend.execute(
            "DELETE FROM workers WHERE last_seen < ?", (cutoff,)
        )
        await self.backend.commit()
        
        # Find active workers
        cursor = await self.backend.execute("""
            SELECT service_type, worker_id, endpoint, capabilities, last_seen, load_score, metadata
            FROM workers 
            WHERE service_type = ?
            ORDER BY load_score ASC
            LIMIT 1
        """, (service_type,))
        
        row = await cursor.fetchone()
        if not row:
            return None
        
        # Convert back to WorkerInfo
        return WorkerInfo(
            service_type=row[0],
            worker_id=row[1],
            endpoint=row[2],
            capabilities=json.loads(row[3]),
            last_seen=datetime.fromisoformat(row[4]),
            load_score=row[5],
            metadata=json.loads(row[6])
        )
    
    async def _find_worker_file(self, service_type: str) -> Optional[WorkerInfo]:
        """Find worker in file storage."""
        workers = self.workers.get(service_type, [])
        if not workers:
            return None
        
        # Filter out stale workers (older than 5 minutes)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        active_workers = []
        
        for worker_data in workers:
            last_seen = datetime.fromisoformat(worker_data['last_seen'])
            if last_seen > cutoff:
                # Convert back to WorkerInfo
                worker_data['last_seen'] = last_seen
                active_workers.append(WorkerInfo(**worker_data))
        
        if not active_workers:
            return None
        
        # Return least loaded worker
        return min(active_workers, key=lambda w: w.load_score)
    
    async def list_workers(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all registered workers by service type."""
        try:
            if self.backend_type == "redis":
                return await self._list_workers_redis()
            elif self.backend_type == "sqlite":
                return await self._list_workers_sqlite()
            elif self.backend_type == "file":
                return await self._list_workers_file()
            else:
                raise ValueError(f"Unknown backend type: {self.backend_type}")
        except Exception as e:
            logger.error(f"❌ Failed to list workers: {e}")
            return {}
    
    async def _list_workers_redis(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all workers from Redis."""
        result = {}
        
        # Get all service keys
        service_keys = await self.backend.keys("service:*")
        
        for service_key in service_keys:
            service_type = service_key.split(":", 1)[1]
            worker_ids = await self.backend.smembers(service_key)
            
            workers = []
            for worker_id in worker_ids:
                worker_key = f"worker:{service_type}:{worker_id}"
                worker_data = await self.backend.hgetall(worker_key)
                
                if worker_data:
                    # Convert for JSON serialization
                    worker_info = {
                        "worker_id": worker_data["worker_id"],
                        "endpoint": worker_data["endpoint"],
                        "capabilities": json.loads(worker_data.get("capabilities", "[]")),
                        "last_seen": worker_data["last_seen"],
                        "load_score": float(worker_data.get("load_score", 0.0))
                    }
                    workers.append(worker_info)
            
            if workers:
                result[service_type] = workers
        
        return result
    
    async def _list_workers_sqlite(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all workers from SQLite."""
        # Clean up stale workers
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
        await self.backend.execute(
            "DELETE FROM workers WHERE last_seen < ?", (cutoff,)
        )
        await self.backend.commit()
        
        # Get active workers
        cursor = await self.backend.execute("""
            SELECT service_type, worker_id, endpoint, capabilities, last_seen, load_score
            FROM workers
            ORDER BY service_type, worker_id
        """)
        
        rows = await cursor.fetchall()
        result = {}
        
        for row in rows:
            service_type = row[0]
            if service_type not in result:
                result[service_type] = []
            
            worker_info = {
                "worker_id": row[1],
                "endpoint": row[2],
                "capabilities": json.loads(row[3]),
                "last_seen": row[4],
                "load_score": row[5]
            }
            result[service_type].append(worker_info)
        
        return result
    
    async def _list_workers_file(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all workers from file storage."""
        result = {}
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=5)
        
        for service_type, workers in self.workers.items():
            active_workers = []
            
            for worker_data in workers:
                last_seen = datetime.fromisoformat(worker_data['last_seen'])
                if last_seen > cutoff:
                    # Convert for JSON serialization
                    worker_info = {
                        "worker_id": worker_data["worker_id"],
                        "endpoint": worker_data["endpoint"],
                        "capabilities": worker_data["capabilities"],
                        "last_seen": worker_data["last_seen"],
                        "load_score": worker_data["load_score"]
                    }
                    active_workers.append(worker_info)
            
            if active_workers:
                result[service_type] = active_workers
        
        return result
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.backend_type == "redis" and self.backend:
            await self.backend.close()
        elif self.backend_type == "sqlite" and self.backend:
            await self.backend.close()
        
        logger.info(f"🧹 Cleaned up {self.backend_type} backend")


# Factory function for easy integration
async def create_discovery_service() -> DiscoveryServiceInterface:
    """Create and initialize the appropriate discovery service."""
    
    # Check if persistence is disabled for testing
    if os.getenv("DISCOVERY_PERSISTENCE", "true").lower() == "false":
        logger.info("🧪 Using in-memory discovery service (testing mode)")
        from platform_service import DiscoveryServiceStub
        return DiscoveryServiceStub()
    
    # Create persistent service
    service = PersistentDiscoveryService()
    await service.initialize()
    return service