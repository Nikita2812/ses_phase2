"""
Feedback Vector Service - Phase 3 Sprint 1
Purpose: Create mistake-correction vector pairs for similarity-based learning
"""

import json
import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from app.core.database import DatabaseConfig
from app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class FeedbackVectorService:
    """
    Creates and manages vector embeddings for mistake-correction pairs.

    This service integrates with the learning pipeline to create searchable
    vector representations of mistakes and their corrections.
    """

    def __init__(self):
        self.db_config = DatabaseConfig()
        self.embedding_service = EmbeddingService()

    async def create_vector_pair(
        self,
        feedback_id: UUID,
        schema_key: str,
        ai_output: Dict[str, Any],
        human_output: Dict[str, Any],
        correction_reason: Optional[str] = None,
        step_name: Optional[str] = None
    ) -> UUID:
        """
        Create a mistake-correction vector pair from feedback.

        Args:
            feedback_id: ID of the feedback log
            schema_key: Deliverable schema key
            ai_output: AI-generated output (mistake)
            human_output: Human-corrected output (correction)
            correction_reason: Reason for correction
            step_name: Name of the workflow step

        Returns:
            Vector pair ID
        """
        try:
            # Generate descriptions for embedding
            mistake_desc = self._generate_mistake_description(
                ai_output, human_output, step_name
            )
            correction_desc = self._generate_correction_description(
                ai_output, human_output, correction_reason, step_name
            )

            logger.info(f"Generating embeddings for feedback {feedback_id}")

            # Generate embeddings
            mistake_embedding = await self.embedding_service.generate_embedding(
                mistake_desc
            )
            correction_embedding = await self.embedding_service.generate_embedding(
                correction_desc
            )

            # Create context metadata
            context_metadata = {
                "schema_key": schema_key,
                "step_name": step_name,
                "correction_reason": correction_reason,
                "fields_modified": list(set(human_output.keys()) - set(ai_output.keys())) +
                                 list(set(ai_output.keys()) - set(human_output.keys())),
                "timestamp": str(datetime.now())
            }

            # Insert vector pair
            query = """
                INSERT INTO csa.feedback_vectors (
                    feedback_id,
                    schema_key,
                    mistake_embedding,
                    correction_embedding,
                    mistake_description,
                    correction_description,
                    context_metadata
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s::jsonb
                ) RETURNING vector_id
            """

            from datetime import datetime
            result = self.db_config.execute_query(query, (
                str(feedback_id),
                schema_key,
                mistake_embedding,
                correction_embedding,
                mistake_desc,
                correction_desc,
                json.dumps(context_metadata)
            ))

            if result and len(result) > 0:
                vector_id = UUID(result[0]['vector_id'])

                # Mark feedback as processed
                await self._mark_feedback_processed(feedback_id, vector_id)

                logger.info(
                    f"Created vector pair {vector_id} for feedback {feedback_id}"
                )

                return vector_id
            else:
                raise Exception("Failed to create vector pair")

        except Exception as e:
            logger.error(f"Error creating vector pair: {e}")
            raise

    async def process_unprocessed_feedback(
        self,
        limit: int = 100,
        force_recreate: bool = False
    ) -> Tuple[int, int, List[UUID]]:
        """
        Process unprocessed feedback to create vector pairs.

        Args:
            limit: Maximum number of feedback items to process
            force_recreate: Force recreate existing vectors

        Returns:
            Tuple of (processed_count, failed_count, vector_ids)
        """
        try:
            # Get unprocessed feedback
            query = """
                SELECT * FROM csa.get_unprocessed_feedback(
                    p_limit := %s
                )
            """

            feedback_items = self.db_config.execute_query(query, (limit,))

            if not feedback_items:
                logger.info("No unprocessed feedback found")
                return (0, 0, [])

            processed_count = 0
            failed_count = 0
            vector_ids = []

            for item in feedback_items:
                try:
                    vector_id = await self.create_vector_pair(
                        feedback_id=UUID(item['feedback_id']),
                        schema_key=item['schema_key'],
                        ai_output=item['ai_output'],
                        human_output=item['human_output'],
                        correction_reason=item.get('correction_reason'),
                        step_name=item.get('step_name')
                    )

                    vector_ids.append(vector_id)
                    processed_count += 1

                except Exception as e:
                    logger.error(
                        f"Failed to process feedback {item['feedback_id']}: {e}"
                    )
                    failed_count += 1

            logger.info(
                f"Processed {processed_count} feedback items, "
                f"failed {failed_count}"
            )

            return (processed_count, failed_count, vector_ids)

        except Exception as e:
            logger.error(f"Error processing unprocessed feedback: {e}")
            raise

    async def search_similar_mistakes(
        self,
        current_output: Dict[str, Any],
        schema_key: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for similar historical mistakes.

        Args:
            current_output: Current output to check
            schema_key: Deliverable schema key
            limit: Maximum number of results

        Returns:
            List of similar mistakes with corrections
        """
        try:
            # Generate description for current output
            current_desc = self._generate_output_description(current_output)

            # Generate embedding
            current_embedding = await self.embedding_service.generate_embedding(
                current_desc
            )

            # Search for similar mistakes
            query = """
                SELECT
                    fv.vector_id,
                    fv.mistake_description,
                    fv.correction_description,
                    fv.context_metadata,
                    fv.effectiveness_score,
                    fl.ai_output,
                    fl.human_output,
                    fl.correction_reason,
                    1 - (fv.mistake_embedding <=> %s::vector) as similarity
                FROM csa.feedback_vectors fv
                JOIN csa.feedback_logs fl ON fv.feedback_id = fl.feedback_id
                WHERE fv.schema_key = %s
                ORDER BY fv.mistake_embedding <=> %s::vector
                LIMIT %s
            """

            results = self.db_config.execute_query(query, (
                current_embedding,
                schema_key,
                current_embedding,
                limit
            ))

            if results:
                # Update retrieval stats
                for result in results:
                    await self._update_retrieval_stats(UUID(result['vector_id']))

                return results
            else:
                return []

        except Exception as e:
            logger.error(f"Error searching similar mistakes: {e}")
            raise

    def _generate_mistake_description(
        self,
        ai_output: Dict[str, Any],
        human_output: Dict[str, Any],
        step_name: Optional[str] = None
    ) -> str:
        """
        Generate a natural language description of the mistake.

        Args:
            ai_output: AI-generated output
            human_output: Human-corrected output
            step_name: Step name

        Returns:
            Description string
        """
        # Find differences
        differences = []
        for key in ai_output.keys():
            if key in human_output and ai_output[key] != human_output[key]:
                differences.append(
                    f"{key}: AI produced {ai_output[key]} but should be {human_output[key]}"
                )

        desc_parts = []
        if step_name:
            desc_parts.append(f"In {step_name} step:")

        if differences:
            desc_parts.append("Incorrect values: " + ", ".join(differences[:3]))
        else:
            desc_parts.append(f"Output structure or values were incorrect")

        return " ".join(desc_parts)

    def _generate_correction_description(
        self,
        ai_output: Dict[str, Any],
        human_output: Dict[str, Any],
        correction_reason: Optional[str],
        step_name: Optional[str] = None
    ) -> str:
        """
        Generate a natural language description of the correction.

        Args:
            ai_output: AI-generated output
            human_output: Human-corrected output
            correction_reason: Reason for correction
            step_name: Step name

        Returns:
            Description string
        """
        desc_parts = []

        if step_name:
            desc_parts.append(f"For {step_name}:")

        if correction_reason:
            desc_parts.append(correction_reason)

        # Add corrected values
        corrections = []
        for key in human_output.keys():
            if key not in ai_output or ai_output[key] != human_output[key]:
                corrections.append(f"{key} should be {human_output[key]}")

        if corrections:
            desc_parts.append("Corrections: " + ", ".join(corrections[:3]))

        return " ".join(desc_parts)

    def _generate_output_description(
        self,
        output: Dict[str, Any]
    ) -> str:
        """
        Generate a description of an output for similarity search.

        Args:
            output: Output dictionary

        Returns:
            Description string
        """
        key_values = [f"{k}: {v}" for k, v in list(output.items())[:5]]
        return "Output contains " + ", ".join(key_values)

    async def _mark_feedback_processed(
        self,
        feedback_id: UUID,
        vector_id: UUID
    ) -> None:
        """Mark feedback as processed."""
        try:
            query = """
                SELECT csa.mark_feedback_processed(
                    p_feedback_id := %s,
                    p_vector_pair_id := %s
                )
            """

            self.db_config.execute_query(query, (
                str(feedback_id),
                str(vector_id)
            ))

        except Exception as e:
            logger.error(f"Error marking feedback processed: {e}")
            raise

    async def _update_retrieval_stats(
        self,
        vector_id: UUID
    ) -> None:
        """Update retrieval statistics for a vector pair."""
        try:
            query = """
                UPDATE csa.feedback_vectors
                SET times_retrieved = times_retrieved + 1,
                    last_retrieved_at = NOW()
                WHERE vector_id = %s
            """

            self.db_config.execute_query(query, (str(vector_id),))

        except Exception as e:
            logger.error(f"Error updating retrieval stats: {e}")
            # Don't raise - this is non-critical

    async def get_effectiveness_metrics(
        self,
        schema_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get effectiveness metrics for vector pairs.

        Args:
            schema_key: Optional schema key filter

        Returns:
            Metrics dictionary
        """
        try:
            query = """
                SELECT
                    COUNT(*) as total_vectors,
                    AVG(times_retrieved) as avg_retrievals,
                    AVG(effectiveness_score) as avg_effectiveness,
                    COUNT(*) FILTER (WHERE times_retrieved > 0) as used_vectors,
                    COUNT(*) FILTER (WHERE effectiveness_score > 0.7) as high_effectiveness_vectors
                FROM csa.feedback_vectors
                WHERE %s IS NULL OR schema_key = %s
            """

            result = self.db_config.execute_query(query, (schema_key, schema_key))

            if result and len(result) > 0:
                return result[0]
            else:
                return {
                    "total_vectors": 0,
                    "avg_retrievals": 0,
                    "avg_effectiveness": 0,
                    "used_vectors": 0,
                    "high_effectiveness_vectors": 0
                }

        except Exception as e:
            logger.error(f"Error getting effectiveness metrics: {e}")
            raise
