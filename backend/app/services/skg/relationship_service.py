"""
Knowledge Relationship Service for the Strategic Knowledge Graph.

Provides functionality for:
- Managing relationships between knowledge entities
- Traversing the knowledge graph
- Finding related entities
- Graph analytics
"""

import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.core.database import DatabaseConfig
from app.schemas.skg.relationship_models import (
    BulkRelationshipCreate,
    BulkRelationshipResult,
    GraphPath,
    GraphPathEdge,
    GraphPathNode,
    GraphPathRequest,
    GraphPathResponse,
    GraphStatistics,
    KnowledgeEntityType,
    KnowledgeRelationship,
    KnowledgeRelationshipCreate,
    RelatedEntitiesResponse,
    RelatedEntity,
    RelatedEntityRequest,
    RelationshipType,
    RelationshipWithDetails,
)

logger = logging.getLogger(__name__)


class KnowledgeRelationshipService:
    """Service for managing relationships in the Strategic Knowledge Graph."""

    def __init__(self):
        """Initialize the relationship service."""
        self.db = DatabaseConfig()

    # =========================================================================
    # RELATIONSHIP CRUD
    # =========================================================================

    def create_relationship(
        self,
        data: KnowledgeRelationshipCreate
    ) -> KnowledgeRelationship:
        """
        Create a relationship between two knowledge entities.

        Args:
            data: Relationship creation data

        Returns:
            Created relationship
        """
        relationship_id = uuid4()

        query = """
        INSERT INTO knowledge_relationships (
            id, source_type, source_id, target_type, target_id,
            relationship_type, strength, description, metadata,
            created_by, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        RETURNING *
        """

        params = (
            str(relationship_id),
            data.source_type.value,
            str(data.source_id),
            data.target_type.value,
            str(data.target_id),
            data.relationship_type.value,
            float(data.strength),
            data.description,
            json.dumps(data.metadata),
            data.created_by,
        )

        result = self.db.execute_query_dict(query, params)

        self.db.log_audit(
            user_id=data.created_by,
            action="create_relationship",
            entity_type="knowledge_relationship",
            entity_id=str(relationship_id),
            details={
                "source_type": data.source_type.value,
                "target_type": data.target_type.value,
                "relationship_type": data.relationship_type.value
            }
        )

        logger.info(
            f"Created relationship: {data.source_type.value}:{data.source_id} "
            f"--[{data.relationship_type.value}]--> "
            f"{data.target_type.value}:{data.target_id}"
        )

        return KnowledgeRelationship(**result[0])

    def get_relationship(
        self,
        relationship_id: UUID
    ) -> Optional[KnowledgeRelationship]:
        """Get a relationship by ID."""
        query = "SELECT * FROM knowledge_relationships WHERE id = %s"
        result = self.db.execute_query_dict(query, (str(relationship_id),))
        return KnowledgeRelationship(**result[0]) if result else None

    def delete_relationship(
        self,
        relationship_id: UUID,
        deleted_by: str
    ) -> bool:
        """Delete a relationship."""
        query = "DELETE FROM knowledge_relationships WHERE id = %s RETURNING id"
        result = self.db.execute_query_dict(query, (str(relationship_id),))

        if result:
            self.db.log_audit(
                user_id=deleted_by,
                action="delete_relationship",
                entity_type="knowledge_relationship",
                entity_id=str(relationship_id),
                details={}
            )
            return True

        return False

    def create_bulk_relationships(
        self,
        data: BulkRelationshipCreate
    ) -> BulkRelationshipResult:
        """Create multiple relationships."""
        created = 0
        skipped = 0
        errors = []

        for rel in data.relationships:
            try:
                # Check if relationship already exists
                existing = self._check_existing_relationship(
                    rel.source_type, rel.source_id,
                    rel.target_type, rel.target_id,
                    rel.relationship_type
                )

                if existing:
                    skipped += 1
                else:
                    self.create_relationship(rel)
                    created += 1

            except Exception as e:
                errors.append({
                    "source": f"{rel.source_type.value}:{rel.source_id}",
                    "target": f"{rel.target_type.value}:{rel.target_id}",
                    "error": str(e)
                })
                logger.error(f"Failed to create relationship: {e}")

        return BulkRelationshipResult(
            total_submitted=len(data.relationships),
            relationships_created=created,
            relationships_skipped=skipped,
            errors=errors
        )

    def _check_existing_relationship(
        self,
        source_type: KnowledgeEntityType,
        source_id: UUID,
        target_type: KnowledgeEntityType,
        target_id: UUID,
        relationship_type: RelationshipType
    ) -> bool:
        """Check if a relationship already exists."""
        query = """
        SELECT 1 FROM knowledge_relationships
        WHERE source_type = %s AND source_id = %s
          AND target_type = %s AND target_id = %s
          AND relationship_type = %s
        LIMIT 1
        """
        params = (
            source_type.value, str(source_id),
            target_type.value, str(target_id),
            relationship_type.value
        )
        result = self.db.execute_query_dict(query, params)
        return len(result) > 0

    # =========================================================================
    # GRAPH QUERIES
    # =========================================================================

    def get_related_entities(
        self,
        request: RelatedEntityRequest
    ) -> RelatedEntitiesResponse:
        """
        Get entities related to a given entity.

        Args:
            request: Request with entity and filters

        Returns:
            Related entities response
        """
        related = []

        # Get outgoing relationships
        outgoing_query = """
        SELECT
            kr.target_type as entity_type,
            kr.target_id as entity_id,
            kr.relationship_type,
            kr.strength,
            'outgoing' as direction
        FROM knowledge_relationships kr
        WHERE kr.source_type = %s AND kr.source_id = %s
        """
        params: List[Any] = [request.entity_type.value, str(request.entity_id)]

        if request.relationship_types:
            placeholders = ','.join(['%s'] * len(request.relationship_types))
            outgoing_query += f" AND kr.relationship_type IN ({placeholders})"
            params.extend([rt.value for rt in request.relationship_types])

        if request.target_types:
            placeholders = ','.join(['%s'] * len(request.target_types))
            outgoing_query += f" AND kr.target_type IN ({placeholders})"
            params.extend([tt.value for tt in request.target_types])

        outgoing_query += " AND kr.strength >= %s"
        params.append(float(request.min_strength))

        outgoing_query += " ORDER BY kr.strength DESC LIMIT %s"
        params.append(request.limit)

        outgoing_results = self.db.execute_query_dict(outgoing_query, tuple(params))

        for row in outgoing_results:
            entity_name, entity_summary = self._get_entity_name_and_summary(
                KnowledgeEntityType(row["entity_type"]),
                UUID(row["entity_id"])
            )
            related.append(RelatedEntity(
                entity_type=KnowledgeEntityType(row["entity_type"]),
                entity_id=UUID(row["entity_id"]),
                entity_name=entity_name,
                entity_summary=entity_summary,
                relationship_type=RelationshipType(row["relationship_type"]),
                relationship_direction="outgoing",
                strength=Decimal(str(row["strength"]))
            ))

        # Get incoming relationships if requested
        if request.include_reverse:
            incoming_query = """
            SELECT
                kr.source_type as entity_type,
                kr.source_id as entity_id,
                kr.relationship_type,
                kr.strength,
                'incoming' as direction
            FROM knowledge_relationships kr
            WHERE kr.target_type = %s AND kr.target_id = %s
            """
            params = [request.entity_type.value, str(request.entity_id)]

            if request.relationship_types:
                placeholders = ','.join(['%s'] * len(request.relationship_types))
                incoming_query += f" AND kr.relationship_type IN ({placeholders})"
                params.extend([rt.value for rt in request.relationship_types])

            if request.target_types:
                placeholders = ','.join(['%s'] * len(request.target_types))
                incoming_query += f" AND kr.source_type IN ({placeholders})"
                params.extend([tt.value for tt in request.target_types])

            incoming_query += " AND kr.strength >= %s"
            params.append(float(request.min_strength))

            incoming_query += " ORDER BY kr.strength DESC LIMIT %s"
            params.append(request.limit)

            incoming_results = self.db.execute_query_dict(incoming_query, tuple(params))

            for row in incoming_results:
                entity_name, entity_summary = self._get_entity_name_and_summary(
                    KnowledgeEntityType(row["entity_type"]),
                    UUID(row["entity_id"])
                )
                related.append(RelatedEntity(
                    entity_type=KnowledgeEntityType(row["entity_type"]),
                    entity_id=UUID(row["entity_id"]),
                    entity_name=entity_name,
                    entity_summary=entity_summary,
                    relationship_type=RelationshipType(row["relationship_type"]),
                    relationship_direction="incoming",
                    strength=Decimal(str(row["strength"]))
                ))

        # Get source entity name
        source_name, _ = self._get_entity_name_and_summary(
            request.entity_type,
            request.entity_id
        )

        return RelatedEntitiesResponse(
            source_type=request.entity_type,
            source_id=request.entity_id,
            source_name=source_name,
            total_relationships=len(related),
            related_entities=related[:request.limit]
        )

    def _get_entity_name_and_summary(
        self,
        entity_type: KnowledgeEntityType,
        entity_id: UUID
    ) -> tuple[str, Optional[str]]:
        """Get the name and summary of an entity."""
        if entity_type == KnowledgeEntityType.COST_ITEM:
            query = "SELECT item_name, item_code FROM cost_items WHERE id = %s"
            result = self.db.execute_query_dict(query, (str(entity_id),))
            if result:
                return result[0]["item_name"], f"Code: {result[0]['item_code']}"

        elif entity_type == KnowledgeEntityType.RULE:
            query = "SELECT rule_name, description FROM constructability_rules WHERE id = %s"
            result = self.db.execute_query_dict(query, (str(entity_id),))
            if result:
                return result[0]["rule_name"], result[0].get("description")

        elif entity_type == KnowledgeEntityType.LESSON:
            query = "SELECT title, issue_description FROM lessons_learned WHERE id = %s"
            result = self.db.execute_query_dict(query, (str(entity_id),))
            if result:
                desc = result[0]["issue_description"]
                summary = desc[:200] + "..." if len(desc) > 200 else desc
                return result[0]["title"], summary

        return "Unknown", None

    def find_paths(
        self,
        request: GraphPathRequest
    ) -> GraphPathResponse:
        """
        Find paths between two entities in the knowledge graph.

        Uses breadth-first search with depth limit.

        Args:
            request: Path finding request

        Returns:
            Found paths
        """
        paths = []

        # BFS to find paths
        visited = set()
        queue = [(
            [(request.start_type, request.start_id)],
            []  # edges
        )]

        while queue and len(paths) < 10:  # Limit to 10 paths
            current_path, current_edges = queue.pop(0)
            current_type, current_id = current_path[-1]

            if len(current_path) > request.max_depth + 1:
                continue

            # Check if we reached the target
            if current_type == request.end_type and current_id == request.end_id:
                if len(current_path) > 1:  # Don't include trivial path
                    path_nodes = []
                    for node_type, node_id in current_path:
                        name, _ = self._get_entity_name_and_summary(node_type, node_id)
                        path_nodes.append(GraphPathNode(
                            entity_type=node_type,
                            entity_id=node_id,
                            entity_name=name
                        ))

                    # Calculate total strength
                    total_strength = Decimal("1.0")
                    for edge in current_edges:
                        total_strength *= edge.strength

                    paths.append(GraphPath(
                        nodes=path_nodes,
                        edges=current_edges,
                        total_strength=total_strength,
                        path_length=len(current_path) - 1
                    ))
                continue

            # Skip if already visited at this depth
            visit_key = (current_type, current_id, len(current_path))
            if visit_key in visited:
                continue
            visited.add(visit_key)

            # Get neighbors
            neighbors = self._get_neighbors(
                current_type,
                current_id,
                request.relationship_types
            )

            for neighbor_type, neighbor_id, rel_type, strength, direction in neighbors:
                if (neighbor_type, neighbor_id) not in [(n[0], n[1]) for n in current_path]:
                    new_path = current_path + [(neighbor_type, neighbor_id)]
                    new_edges = current_edges + [GraphPathEdge(
                        relationship_type=rel_type,
                        strength=strength,
                        direction=direction
                    )]
                    queue.append((new_path, new_edges))

        # Get start and end entity names
        start_name, _ = self._get_entity_name_and_summary(
            request.start_type,
            request.start_id
        )
        end_name, _ = self._get_entity_name_and_summary(
            request.end_type,
            request.end_id
        )

        return GraphPathResponse(
            start_entity=GraphPathNode(
                entity_type=request.start_type,
                entity_id=request.start_id,
                entity_name=start_name
            ),
            end_entity=GraphPathNode(
                entity_type=request.end_type,
                entity_id=request.end_id,
                entity_name=end_name
            ),
            paths_found=len(paths),
            paths=sorted(paths, key=lambda p: (-p.total_strength, p.path_length))
        )

    def _get_neighbors(
        self,
        entity_type: KnowledgeEntityType,
        entity_id: UUID,
        relationship_types: Optional[List[RelationshipType]]
    ) -> List[tuple]:
        """Get neighbors of an entity in the graph."""
        neighbors = []

        # Outgoing
        query = """
        SELECT target_type, target_id, relationship_type, strength
        FROM knowledge_relationships
        WHERE source_type = %s AND source_id = %s
        """
        params: List[Any] = [entity_type.value, str(entity_id)]

        if relationship_types:
            placeholders = ','.join(['%s'] * len(relationship_types))
            query += f" AND relationship_type IN ({placeholders})"
            params.extend([rt.value for rt in relationship_types])

        result = self.db.execute_query_dict(query, tuple(params))
        for row in result:
            neighbors.append((
                KnowledgeEntityType(row["target_type"]),
                UUID(row["target_id"]),
                RelationshipType(row["relationship_type"]),
                Decimal(str(row["strength"])),
                "forward"
            ))

        # Incoming
        query = """
        SELECT source_type, source_id, relationship_type, strength
        FROM knowledge_relationships
        WHERE target_type = %s AND target_id = %s
        """
        params = [entity_type.value, str(entity_id)]

        if relationship_types:
            placeholders = ','.join(['%s'] * len(relationship_types))
            query += f" AND relationship_type IN ({placeholders})"
            params.extend([rt.value for rt in relationship_types])

        result = self.db.execute_query_dict(query, tuple(params))
        for row in result:
            neighbors.append((
                KnowledgeEntityType(row["source_type"]),
                UUID(row["source_id"]),
                RelationshipType(row["relationship_type"]),
                Decimal(str(row["strength"])),
                "reverse"
            ))

        return neighbors

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(self) -> GraphStatistics:
        """Get statistics about the knowledge graph."""
        # Get SKG stats using helper function
        stats_query = "SELECT * FROM get_skg_stats()"
        stats_result = self.db.execute_query_dict(stats_query)
        stats_dict = {row["stat_name"]: row["stat_value"] for row in stats_result}

        # Relationships by type
        rel_type_query = """
        SELECT relationship_type, COUNT(*) as count
        FROM knowledge_relationships
        GROUP BY relationship_type
        """
        rel_type_result = self.db.execute_query_dict(rel_type_query)
        relationships_by_type = {
            row["relationship_type"]: row["count"]
            for row in rel_type_result
        }

        # Total entities
        total_entities = (
            stats_dict.get("total_cost_items", 0) +
            stats_dict.get("total_rules", 0) +
            stats_dict.get("total_lessons", 0)
        )

        # Average relationships per entity
        total_relationships = stats_dict.get("total_relationships", 0)
        avg_relationships = (
            total_relationships / total_entities if total_entities > 0 else 0
        )

        # Most connected entities
        most_connected_query = """
        WITH entity_counts AS (
            SELECT source_type as entity_type, source_id as entity_id, COUNT(*) as count
            FROM knowledge_relationships
            GROUP BY source_type, source_id
            UNION ALL
            SELECT target_type, target_id, COUNT(*)
            FROM knowledge_relationships
            GROUP BY target_type, target_id
        )
        SELECT entity_type, entity_id, SUM(count) as total_connections
        FROM entity_counts
        GROUP BY entity_type, entity_id
        ORDER BY total_connections DESC
        LIMIT 10
        """
        most_connected_result = self.db.execute_query_dict(most_connected_query)
        most_connected = []
        for row in most_connected_result:
            name, _ = self._get_entity_name_and_summary(
                KnowledgeEntityType(row["entity_type"]),
                UUID(row["entity_id"])
            )
            most_connected.append({
                "entity_type": row["entity_type"],
                "entity_id": str(row["entity_id"]),
                "entity_name": name,
                "connections": row["total_connections"]
            })

        # Recently added (last 7 days)
        recent_query = """
        SELECT
            'cost_items' as entity_type,
            COUNT(*) as count
        FROM cost_items
        WHERE created_at > NOW() - INTERVAL '7 days'
        UNION ALL
        SELECT
            'rules',
            COUNT(*)
        FROM constructability_rules
        WHERE created_at > NOW() - INTERVAL '7 days'
        UNION ALL
        SELECT
            'lessons',
            COUNT(*)
        FROM lessons_learned
        WHERE created_at > NOW() - INTERVAL '7 days'
        """
        recent_result = self.db.execute_query_dict(recent_query)
        recently_added = {row["entity_type"]: row["count"] for row in recent_result}

        return GraphStatistics(
            total_cost_items=stats_dict.get("total_cost_items", 0),
            total_rules=stats_dict.get("total_rules", 0),
            total_lessons=stats_dict.get("total_lessons", 0),
            total_relationships=total_relationships,
            relationships_by_type=relationships_by_type,
            avg_relationships_per_entity=round(avg_relationships, 2),
            most_connected_entities=most_connected,
            recently_added=recently_added
        )
