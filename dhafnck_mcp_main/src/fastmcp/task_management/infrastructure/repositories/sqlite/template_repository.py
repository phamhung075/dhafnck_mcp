"""SQLite Template Repository Implementation"""

import sqlite3
import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path

from ....domain.entities.template import Template, TemplateUsage
from ....domain.value_objects.template_id import TemplateId
from ....domain.enums.template_enums import TemplateType, TemplateCategory, TemplateStatus, TemplatePriority
from ....domain.repositories.template_repository import TemplateRepositoryInterface
# Removed problematic tool_path import
from ...database.database_source_manager import get_database_path, get_database_info

logger = logging.getLogger(__name__)


def _find_project_root() -> Path:
    """Find project root by looking for dhafnck_mcp_main directory"""
    current_path = Path(__file__).resolve()
    
    # Walk up the directory tree looking for dhafnck_mcp_main
    while current_path.parent != current_path:
        if (current_path / "dhafnck_mcp_main").exists():
            return current_path
        current_path = current_path.parent
    
    # If not found, use current working directory as fallback
    cwd = Path.cwd()
    if (cwd / "dhafnck_mcp_main").exists():
        return cwd
        
    # Last resort - use the directory containing dhafnck_mcp_main
    current_path = Path(__file__).resolve()
    while current_path.parent != current_path:
        if current_path.name == "dhafnck_mcp_main":
            return current_path.parent
        current_path = current_path.parent
    
    # Absolute fallback
    return Path("/home/daihungpham/agentic-project")


class SQLiteTemplateRepository(TemplateRepositoryInterface):
    """SQLite implementation of template repository"""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize SQLite template repository"""
        # Resolve database path
        if db_path:
            project_root = _find_project_root()
            if Path(db_path).is_absolute():
                self._db_path = str(db_path)
            else:
                self._db_path = str(project_root / db_path)
        else:
            self._db_path = get_database_path()
        
        db_info = get_database_info()
        logger.info(f"SQLiteTemplateRepository using db_path: {self._db_path}")
        logger.info(f"Database mode: {db_info['mode']}, is_test: {db_info['is_test']}")
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        
        # Create schema
        self._create_schema()
    
    def _get_connection(self):
        """Get database connection with row factory for dict-like access"""
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _create_schema(self):
        """Create the templates and template_usage tables if they don't exist"""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS templates (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    content TEXT NOT NULL,
                    variables TEXT,
                    metadata TEXT,
                    version INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    compatible_agents TEXT,
                    file_patterns TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS template_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    template_id TEXT NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    used_by TEXT,
                    context TEXT,
                    task_id TEXT,
                    project_id TEXT,
                    agent_name TEXT,
                    variables_used TEXT,
                    output_path TEXT,
                    generation_time_ms INTEGER,
                    cache_hit INTEGER,
                    FOREIGN KEY (template_id) REFERENCES templates(id)
                )
            """)
            
            # Create indexes after tables are created
            conn.execute("CREATE INDEX IF NOT EXISTS idx_templates_type ON templates(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_templates_category ON templates(category)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_templates_status ON templates(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_template_usage_template_id ON template_usage(template_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_template_usage_used_at ON template_usage(used_at)")
            
            conn.commit()
    
    def save(self, template: Template) -> Template:
        """Save template to database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id FROM templates WHERE id = ?",
                    (template.id.value,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    conn.execute("""
                        UPDATE templates SET
                            name = ?, description = ?, type = ?, category = ?, status = ?,
                            priority = ?, content = ?, variables = ?, metadata = ?,
                            version = ?, updated_at = ?, is_active = ?,
                            compatible_agents = ?, file_patterns = ?
                        WHERE id = ?
                    """, (
                        template.name, template.description, template.template_type.value,
                        template.category.value, template.status.value, template.priority.value,
                        template.content, json.dumps(template.variables),
                        json.dumps(template.metadata), template.version,
                        template.updated_at.isoformat(), 1 if template.is_active else 0,
                        json.dumps(template.compatible_agents), json.dumps(template.file_patterns),
                        template.id.value
                    ))
                else:
                    conn.execute("""
                        INSERT INTO templates (
                            id, name, description, type, category, status, priority,
                            content, variables, metadata, version, created_at, updated_at,
                            is_active, compatible_agents, file_patterns
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        template.id.value, template.name, template.description,
                        template.template_type.value, template.category.value,
                        template.status.value, template.priority.value, template.content,
                        json.dumps(template.variables), json.dumps(template.metadata),
                        template.version, template.created_at.isoformat(),
                        template.updated_at.isoformat(), 1 if template.is_active else 0,
                        json.dumps(template.compatible_agents), json.dumps(template.file_patterns)
                    ))
                
                conn.commit()
                return template
                
        except Exception as e:
            logger.error(f"Failed to save template {template.id.value}: {e}")
            raise
    
    def get_by_id(self, template_id: TemplateId) -> Optional[Template]:
        """Get template by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM templates WHERE id = ?",
                    (template_id.value,)
                )
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                return self._row_to_template(row)
                
        except Exception as e:
            logger.error(f"Failed to get template {template_id.value}: {e}")
            return None
    
    def list_templates(
        self,
        template_type: Optional[str] = None,
        category: Optional[str] = None,
        agent_compatible: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Template], int]:
        """List templates with filtering and pagination"""
        try:
            with self._get_connection() as conn:
                query_parts = ["SELECT * FROM templates WHERE 1=1"]
                count_parts = ["SELECT COUNT(*) FROM templates WHERE 1=1"]
                params = []
                
                if template_type:
                    query_parts.append("AND type = ?")
                    count_parts.append("AND type = ?")
                    params.append(template_type)
                
                if category:
                    query_parts.append("AND category = ?")
                    count_parts.append("AND category = ?")
                    params.append(category)
                
                if is_active is not None:
                    query_parts.append("AND is_active = ?")
                    count_parts.append("AND is_active = ?")
                    params.append(1 if is_active else 0)
                
                count_query = " ".join(count_parts)
                cursor = conn.execute(count_query, params)
                total_count = cursor.fetchone()[0]
                
                query_parts.append("ORDER BY created_at DESC")
                query_parts.append("LIMIT ? OFFSET ?")
                query = " ".join(query_parts)
                
                cursor = conn.execute(query, params + [limit, offset])
                rows = cursor.fetchall()
                
                templates = []
                for row in rows:
                    template = self._row_to_template(row)
                    
                    if agent_compatible:
                        if not template.is_compatible_with_agent(agent_compatible):
                            continue
                    
                    templates.append(template)
                
                return templates, total_count
                
        except Exception as e:
            logger.error(f"Failed to list templates: {e}")
            return [], 0
    
    def delete(self, template_id: TemplateId) -> bool:
        """Delete template"""
        try:
            with self._get_connection() as conn:
                conn.execute(
                    "DELETE FROM template_usage WHERE template_id = ?",
                    (template_id.value,)
                )
                
                cursor = conn.execute(
                    "DELETE FROM templates WHERE id = ?",
                    (template_id.value,)
                )
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to delete template {template_id.value}: {e}")
            return False
    
    def save_usage(self, usage: TemplateUsage) -> bool:
        """Save template usage record"""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO template_usage (
                        template_id, used_at, used_by, context, task_id, project_id,
                        agent_name, variables_used, output_path, generation_time_ms, cache_hit
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    usage.template_id.value,
                    usage.used_at.isoformat(),
                    usage.agent_name,
                    json.dumps({
                        "task_id": usage.task_id,
                        "project_id": usage.project_id
                    }),
                    usage.task_id,
                    usage.project_id,
                    usage.agent_name,
                    json.dumps(usage.variables_used),
                    usage.output_path,
                    usage.generation_time_ms,
                    1 if usage.cache_hit else 0
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to save usage for template {usage.template_id.value}: {e}")
            return False
    
    def get_usage_stats(self, template_id: TemplateId) -> Dict[str, Any]:
        """Get usage statistics for template"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM template_usage WHERE template_id = ?",
                    (template_id.value,)
                )
                usage_count = cursor.fetchone()[0]
                
                cursor = conn.execute(
                    "SELECT AVG(generation_time_ms) FROM template_usage WHERE template_id = ?",
                    (template_id.value,)
                )
                avg_generation_time = cursor.fetchone()[0] or 0.0
                
                cursor = conn.execute("""
                    SELECT 
                        SUM(CASE WHEN cache_hit = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
                    FROM template_usage 
                    WHERE template_id = ?
                """, (template_id.value,))
                cache_hit_rate = cursor.fetchone()[0] or 0.0
                
                return {
                    'usage_count': usage_count,
                    'success_rate': 100.0,
                    'avg_generation_time': avg_generation_time,
                    'cache_hit_rate': cache_hit_rate
                }
                
        except Exception as e:
            logger.error(f"Failed to get usage stats for template {template_id.value}: {e}")
            return {}
    
    def get_analytics(self, template_id: Optional[str] = None) -> Dict[str, Any]:
        """Get template analytics"""
        try:
            with self._get_connection() as conn:
                if template_id:
                    return self.get_usage_stats(TemplateId(template_id))
                else:
                    cursor = conn.execute("SELECT COUNT(*) FROM templates")
                    total_templates = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM templates WHERE is_active = 1")
                    active_templates = cursor.fetchone()[0]
                    
                    cursor = conn.execute("SELECT COUNT(*) FROM template_usage")
                    total_usage = cursor.fetchone()[0]
                    
                    cursor = conn.execute("""
                        SELECT template_id, COUNT(*) as usage_count
                        FROM template_usage
                        GROUP BY template_id
                        ORDER BY usage_count DESC
                        LIMIT 10
                    """)
                    
                    most_used = []
                    for row in cursor.fetchall():
                        most_used.append({
                            'template_id': row[0],
                            'usage_count': row[1]
                        })
                    
                    return {
                        'total_templates': total_templates,
                        'active_templates': active_templates,
                        'total_usage': total_usage,
                        'most_used_templates': most_used
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return {}
    
    def _row_to_template(self, row: sqlite3.Row) -> Template:
        """Convert database row to Template entity"""
        try:
            variables = json.loads(row['variables']) if row['variables'] else []
            metadata = json.loads(row['metadata']) if row['metadata'] else {}
            compatible_agents = json.loads(row['compatible_agents']) if row['compatible_agents'] else ['*']
            file_patterns = json.loads(row['file_patterns']) if row['file_patterns'] else []
            
            return Template(
                id=TemplateId(row['id']),
                name=row['name'],
                description=row['description'],
                content=row['content'],
                template_type=TemplateType(row['type']),
                category=TemplateCategory(row['category']),
                status=TemplateStatus(row['status']),
                priority=TemplatePriority(row['priority']),
                compatible_agents=compatible_agents,
                file_patterns=file_patterns,
                variables=variables,
                metadata=metadata,
                created_at=datetime.fromisoformat(row['created_at']) if isinstance(row['created_at'], str) else row['created_at'],
                updated_at=datetime.fromisoformat(row['updated_at']) if isinstance(row['updated_at'], str) else row['updated_at'],
                version=row['version'],
                is_active=bool(row['is_active'])
            )
        except Exception as e:
            logger.error(f"Failed to convert row to template: {e}")
            raise