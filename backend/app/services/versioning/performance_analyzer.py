"""
Phase 3 Sprint 4: A/B TESTING & VERSIONING
Performance Analyzer - Statistical Analysis for A/B Testing

This module provides:
1. Statistical comparison of versions/variants
2. Significance testing (t-test, chi-squared)
3. Confidence interval calculation
4. Effect size computation (Cohen's d)
5. Performance trend analysis
"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import math
from dataclasses import dataclass

from app.schemas.versioning.models import (
    VersionComparison,
    VersionComparisonRequest,
    StatisticalResult,
    ConfidenceInterval,
    SchemaPerformanceSummary,
    PerformanceTrend,
    MetricComparison
)
from app.core.database import DatabaseConfig


@dataclass
class SampleStats:
    """Statistics for a sample."""
    n: int
    mean: float
    std_dev: float
    success_count: int = 0
    failure_count: int = 0


class PerformanceAnalyzer:
    """
    Analyzer for schema version and variant performance.

    Key Features:
    - Compare performance between versions/variants
    - Calculate statistical significance
    - Generate performance trends
    - Provide recommendations
    """

    def __init__(self):
        """Initialize analyzer with database connection."""
        self.db = DatabaseConfig()

    # ========================================================================
    # VERSION COMPARISON
    # ========================================================================

    def compare_versions(
        self,
        request: VersionComparisonRequest,
        compared_by: str
    ) -> VersionComparison:
        """
        Compare two schema versions with statistical analysis.

        Args:
            request: Comparison request with version details
            compared_by: User requesting comparison

        Returns:
            VersionComparison with statistical results

        Raises:
            ValueError: If insufficient data for comparison
        """
        from uuid import uuid4

        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=request.period_days)

        # Get execution data for both versions
        baseline_stats = self._get_version_stats(
            request.schema_id,
            request.baseline_version,
            request.baseline_variant_id,
            period_start,
            period_end
        )

        comparison_stats = self._get_version_stats(
            request.schema_id,
            request.comparison_version,
            request.comparison_variant_id,
            period_start,
            period_end
        )

        # Validate sample sizes
        if baseline_stats['total'] < 10:
            raise ValueError(
                f"Insufficient baseline data: {baseline_stats['total']} executions "
                f"(minimum 10 required)"
            )

        if comparison_stats['total'] < 10:
            raise ValueError(
                f"Insufficient comparison data: {comparison_stats['total']} executions "
                f"(minimum 10 required)"
            )

        # Analyze each metric
        metric_results = []
        primary_result = None

        for metric in request.metrics:
            result = self._analyze_metric(
                metric,
                baseline_stats,
                comparison_stats
            )
            metric_results.append(result)

            if metric == request.metrics[0]:  # First metric is primary
                primary_result = result

        # Determine recommendation
        recommendation, reason = self._make_recommendation(
            metric_results,
            baseline_stats['total'],
            comparison_stats['total']
        )

        # Create comparison record
        comparison_id = uuid4()

        comparison = VersionComparison(
            id=comparison_id,
            schema_id=request.schema_id,
            baseline_version=request.baseline_version,
            comparison_version=request.comparison_version,
            baseline_variant_id=request.baseline_variant_id,
            comparison_variant_id=request.comparison_variant_id,
            period_start=period_start,
            period_end=period_end,
            baseline_sample_size=baseline_stats['total'],
            comparison_sample_size=comparison_stats['total'],
            primary_metric=request.metrics[0],
            primary_result=primary_result,
            metric_results=metric_results,
            recommendation=recommendation,
            recommendation_reason=reason,
            created_at=datetime.utcnow(),
            created_by=compared_by
        )

        # Store comparison result
        self._store_comparison(comparison)

        return comparison

    def _get_version_stats(
        self,
        schema_id: UUID,
        version: int,
        variant_id: Optional[UUID],
        period_start: datetime,
        period_end: datetime
    ) -> Dict[str, Any]:
        """Get execution statistics for a version/variant."""
        variant_condition = "AND variant_id = %s" if variant_id else "AND variant_id IS NULL"
        params = [schema_id, period_start, period_end]
        if variant_id:
            params.append(variant_id)

        query = f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE execution_status IN ('completed', 'approved')) as successful,
                COUNT(*) FILTER (WHERE execution_status = 'failed') as failed,
                AVG(execution_time_ms) as avg_time,
                STDDEV(execution_time_ms) as std_time,
                AVG(risk_score) as avg_risk,
                STDDEV(risk_score) as std_risk,
                ARRAY_AGG(execution_time_ms) FILTER (WHERE execution_time_ms IS NOT NULL) as times,
                ARRAY_AGG(risk_score) FILTER (WHERE risk_score IS NOT NULL) as risks
            FROM csa.workflow_executions
            WHERE schema_id = %s
              AND created_at >= %s
              AND created_at < %s
              {variant_condition};
        """

        result = self.db.execute_query_dict(query, tuple(params))

        if not result or not result[0]:
            return {
                'total': 0,
                'successful': 0,
                'failed': 0,
                'avg_time': 0,
                'std_time': 0,
                'avg_risk': 0,
                'std_risk': 0,
                'times': [],
                'risks': []
            }

        row = result[0]
        return {
            'total': row.get('total', 0) or 0,
            'successful': row.get('successful', 0) or 0,
            'failed': row.get('failed', 0) or 0,
            'avg_time': float(row['avg_time']) if row.get('avg_time') else 0,
            'std_time': float(row['std_time']) if row.get('std_time') else 0,
            'avg_risk': float(row['avg_risk']) if row.get('avg_risk') else 0,
            'std_risk': float(row['std_risk']) if row.get('std_risk') else 0,
            'times': row.get('times', []) or [],
            'risks': row.get('risks', []) or []
        }

    def _analyze_metric(
        self,
        metric: str,
        baseline_stats: Dict[str, Any],
        comparison_stats: Dict[str, Any]
    ) -> StatisticalResult:
        """Analyze a single metric between two samples."""
        if metric == "success_rate":
            return self._analyze_proportion(
                metric,
                baseline_stats['successful'],
                baseline_stats['total'],
                comparison_stats['successful'],
                comparison_stats['total']
            )
        elif metric == "execution_time":
            return self._analyze_continuous(
                metric,
                baseline_stats['avg_time'],
                baseline_stats['std_time'],
                baseline_stats['total'],
                comparison_stats['avg_time'],
                comparison_stats['std_time'],
                comparison_stats['total'],
                lower_is_better=True
            )
        elif metric == "risk_score":
            return self._analyze_continuous(
                metric,
                baseline_stats['avg_risk'],
                baseline_stats['std_risk'],
                baseline_stats['total'],
                comparison_stats['avg_risk'],
                comparison_stats['std_risk'],
                comparison_stats['total'],
                lower_is_better=True
            )
        else:
            # Default: treat as continuous metric
            return StatisticalResult(
                metric_name=metric,
                baseline_value=0,
                comparison_value=0,
                absolute_difference=0,
                sample_size_baseline=baseline_stats['total'],
                sample_size_comparison=comparison_stats['total'],
                is_significant=False
            )

    def _analyze_proportion(
        self,
        metric_name: str,
        baseline_successes: int,
        baseline_total: int,
        comparison_successes: int,
        comparison_total: int
    ) -> StatisticalResult:
        """
        Analyze proportions using chi-squared test.

        Used for success rate comparison.
        """
        # Calculate proportions
        p1 = baseline_successes / baseline_total if baseline_total > 0 else 0
        p2 = comparison_successes / comparison_total if comparison_total > 0 else 0

        abs_diff = p2 - p1
        rel_diff = (abs_diff / p1 * 100) if p1 > 0 else None

        # Calculate pooled proportion
        pooled = (baseline_successes + comparison_successes) / (baseline_total + comparison_total)

        # Standard error of difference
        se = math.sqrt(
            pooled * (1 - pooled) * (1/baseline_total + 1/comparison_total)
        ) if pooled > 0 and pooled < 1 else 0

        # Z-score
        z_score = abs_diff / se if se > 0 else 0

        # Two-tailed p-value (approximation using normal distribution)
        p_value = 2 * (1 - self._normal_cdf(abs(z_score)))

        # 95% confidence interval
        ci_margin = 1.96 * se
        ci = ConfidenceInterval(
            lower=abs_diff - ci_margin,
            upper=abs_diff + ci_margin,
            confidence_level=0.95
        )

        # Effect size (Cohen's h for proportions)
        effect_size = self._cohens_h(p1, p2)

        return StatisticalResult(
            metric_name=metric_name,
            baseline_value=p1,
            comparison_value=p2,
            absolute_difference=abs_diff,
            relative_difference=rel_diff,
            p_value=p_value,
            confidence_interval=ci,
            effect_size=effect_size,
            is_significant=p_value < 0.05,
            sample_size_baseline=baseline_total,
            sample_size_comparison=comparison_total
        )

    def _analyze_continuous(
        self,
        metric_name: str,
        baseline_mean: float,
        baseline_std: float,
        baseline_n: int,
        comparison_mean: float,
        comparison_std: float,
        comparison_n: int,
        lower_is_better: bool = False
    ) -> StatisticalResult:
        """
        Analyze continuous metrics using Welch's t-test.

        Used for execution time, risk score, etc.
        """
        abs_diff = comparison_mean - baseline_mean
        rel_diff = (abs_diff / baseline_mean * 100) if baseline_mean != 0 else None

        # Welch's t-test
        if baseline_std == 0 and comparison_std == 0:
            t_stat = 0
            p_value = 1.0
        else:
            se = math.sqrt(
                (baseline_std**2 / baseline_n) + (comparison_std**2 / comparison_n)
            ) if baseline_n > 0 and comparison_n > 0 else 0

            t_stat = abs_diff / se if se > 0 else 0

            # Welch-Satterthwaite degrees of freedom
            df = self._welch_df(
                baseline_std, baseline_n,
                comparison_std, comparison_n
            )

            # Two-tailed p-value (t-distribution approximation)
            p_value = 2 * (1 - self._t_cdf(abs(t_stat), df))

        # 95% confidence interval
        se = math.sqrt(
            (baseline_std**2 / baseline_n) + (comparison_std**2 / comparison_n)
        ) if baseline_n > 0 and comparison_n > 0 else 0
        ci_margin = 1.96 * se
        ci = ConfidenceInterval(
            lower=abs_diff - ci_margin,
            upper=abs_diff + ci_margin,
            confidence_level=0.95
        )

        # Effect size (Cohen's d)
        pooled_std = math.sqrt(
            ((baseline_n - 1) * baseline_std**2 + (comparison_n - 1) * comparison_std**2)
            / (baseline_n + comparison_n - 2)
        ) if baseline_n + comparison_n > 2 else 1
        effect_size = abs_diff / pooled_std if pooled_std > 0 else 0

        return StatisticalResult(
            metric_name=metric_name,
            baseline_value=baseline_mean,
            comparison_value=comparison_mean,
            absolute_difference=abs_diff,
            relative_difference=rel_diff,
            p_value=p_value,
            confidence_interval=ci,
            effect_size=effect_size,
            is_significant=p_value < 0.05,
            sample_size_baseline=baseline_n,
            sample_size_comparison=comparison_n
        )

    def _make_recommendation(
        self,
        metric_results: List[StatisticalResult],
        baseline_n: int,
        comparison_n: int
    ) -> Tuple[str, str]:
        """Make a recommendation based on statistical results."""
        min_sample = 100

        # Check sample size
        if baseline_n < min_sample or comparison_n < min_sample:
            return (
                "needs_more_data",
                f"Insufficient sample size. Need at least {min_sample} executions per version. "
                f"Baseline: {baseline_n}, Comparison: {comparison_n}"
            )

        # Count significant improvements
        significant_improvements = 0
        significant_regressions = 0

        for result in metric_results:
            if result.is_significant:
                # Determine if improvement based on metric type
                is_improvement = False
                if result.metric_name == "success_rate":
                    is_improvement = result.absolute_difference > 0
                else:  # execution_time, risk_score (lower is better)
                    is_improvement = result.absolute_difference < 0

                if is_improvement:
                    significant_improvements += 1
                else:
                    significant_regressions += 1

        # Make recommendation
        if significant_regressions > 0:
            return (
                "keep_baseline",
                f"Comparison version shows {significant_regressions} significant regression(s). "
                f"Recommend keeping baseline."
            )
        elif significant_improvements > 0:
            return (
                "adopt_comparison",
                f"Comparison version shows {significant_improvements} significant improvement(s). "
                f"Recommend adopting comparison version."
            )
        else:
            return (
                "inconclusive",
                "No statistically significant differences detected between versions. "
                "Consider running experiment longer or with more traffic."
            )

    def _store_comparison(self, comparison: VersionComparison) -> None:
        """Store comparison result in database."""
        import json

        query = """
            INSERT INTO csa.version_comparisons (
                id, schema_id, baseline_version, comparison_version,
                baseline_variant_id, comparison_variant_id,
                period_start, period_end,
                baseline_sample_size, comparison_sample_size,
                primary_metric, baseline_value, comparison_value,
                absolute_difference, relative_difference,
                p_value, confidence_interval_lower, confidence_interval_upper,
                effect_size, is_significant,
                secondary_metrics, recommendation, recommendation_reason,
                created_at, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """

        self.db.execute_query(
            query,
            (
                comparison.id,
                comparison.schema_id,
                comparison.baseline_version,
                comparison.comparison_version,
                comparison.baseline_variant_id,
                comparison.comparison_variant_id,
                comparison.period_start,
                comparison.period_end,
                comparison.baseline_sample_size,
                comparison.comparison_sample_size,
                comparison.primary_metric,
                comparison.primary_result.baseline_value,
                comparison.primary_result.comparison_value,
                comparison.primary_result.absolute_difference,
                comparison.primary_result.relative_difference,
                comparison.primary_result.p_value,
                comparison.primary_result.confidence_interval.lower if comparison.primary_result.confidence_interval else None,
                comparison.primary_result.confidence_interval.upper if comparison.primary_result.confidence_interval else None,
                comparison.primary_result.effect_size,
                comparison.primary_result.is_significant,
                json.dumps([r.model_dump() for r in comparison.metric_results]),
                comparison.recommendation,
                comparison.recommendation_reason,
                comparison.created_at,
                comparison.created_by
            ),
            fetch=False
        )

    # ========================================================================
    # PERFORMANCE TRENDS
    # ========================================================================

    def get_performance_summary(
        self,
        schema_id: UUID
    ) -> SchemaPerformanceSummary:
        """
        Get performance summary for a schema.

        Args:
            schema_id: Schema to analyze

        Returns:
            SchemaPerformanceSummary with trends
        """
        # Get schema details
        schema_query = """
            SELECT id, deliverable_type, display_name, discipline, version, status
            FROM csa.deliverable_schemas
            WHERE id = %s;
        """
        schema_result = self.db.execute_query_dict(schema_query, (schema_id,))

        if not schema_result:
            raise ValueError(f"Schema {schema_id} not found")

        schema = schema_result[0]

        # Get overall stats
        stats_query = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE execution_status IN ('completed', 'approved')) as successful,
                COUNT(*) FILTER (WHERE execution_status = 'failed') as failed,
                AVG(execution_time_ms) as avg_time,
                AVG(risk_score) as avg_risk
            FROM csa.workflow_executions
            WHERE schema_id = %s;
        """
        stats_result = self.db.execute_query_dict(stats_query, (schema_id,))
        stats = stats_result[0] if stats_result else {}

        # Get variant/experiment counts
        variant_query = """
            SELECT COUNT(*) FROM csa.schema_variants
            WHERE schema_id = %s AND status = 'active';
        """
        variant_result = self.db.execute_query(variant_query, (schema_id,))
        active_variants = variant_result[0][0] if variant_result else 0

        experiment_query = """
            SELECT COUNT(*) FROM csa.experiments
            WHERE schema_id = %s AND status = 'running';
        """
        experiment_result = self.db.execute_query(experiment_query, (schema_id,))
        active_experiments = experiment_result[0][0] if experiment_result else 0

        # Get trends (last 7 days)
        trends = self.get_performance_trends(schema_id, days=7)

        # Calculate trend direction
        execution_trend = "stable"
        success_rate_trend = "stable"

        if len(trends) >= 2:
            first_half = trends[:len(trends)//2]
            second_half = trends[len(trends)//2:]

            avg_first = sum(t.total_executions for t in first_half) / len(first_half)
            avg_second = sum(t.total_executions for t in second_half) / len(second_half)

            if avg_second > avg_first * 1.1:
                execution_trend = "up"
            elif avg_second < avg_first * 0.9:
                execution_trend = "down"

        total = stats.get('total', 0) or 0
        successful = stats.get('successful', 0) or 0

        return SchemaPerformanceSummary(
            schema_id=schema['id'],
            deliverable_type=schema['deliverable_type'],
            display_name=schema['display_name'],
            discipline=schema['discipline'],
            current_version=schema['version'],
            status=schema['status'],
            total_executions=total,
            successful_executions=successful,
            failed_executions=stats.get('failed', 0) or 0,
            avg_execution_time_ms=float(stats['avg_time']) if stats.get('avg_time') else None,
            avg_risk_score=float(stats['avg_risk']) if stats.get('avg_risk') else None,
            success_rate=successful / total if total > 0 else None,
            active_variants=active_variants,
            active_experiments=active_experiments,
            execution_trend=execution_trend,
            success_rate_trend=success_rate_trend,
            recent_trends=trends
        )

    def get_performance_trends(
        self,
        schema_id: UUID,
        days: int = 30,
        variant_id: Optional[UUID] = None
    ) -> List[PerformanceTrend]:
        """
        Get daily performance trends for a schema.

        Args:
            schema_id: Schema to analyze
            days: Number of days of history
            variant_id: Optional variant filter

        Returns:
            List of PerformanceTrend by day
        """
        variant_condition = "AND variant_id = %s" if variant_id else ""
        params = [schema_id, days]
        if variant_id:
            params.append(variant_id)

        query = f"""
            SELECT
                DATE(created_at) as period,
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE execution_status IN ('completed', 'approved')) as successful,
                COUNT(*) FILTER (WHERE execution_status = 'failed') as failed,
                AVG(execution_time_ms) as avg_time,
                AVG(risk_score) as avg_risk
            FROM csa.workflow_executions
            WHERE schema_id = %s
              AND created_at >= NOW() - (%s || ' days')::INTERVAL
              {variant_condition}
            GROUP BY DATE(created_at)
            ORDER BY period DESC;
        """

        result = self.db.execute_query_dict(query, tuple(params))

        trends = []
        for row in result:
            total = row.get('total', 0) or 0
            successful = row.get('successful', 0) or 0

            trends.append(PerformanceTrend(
                period=row['period'].isoformat() if hasattr(row['period'], 'isoformat') else str(row['period']),
                total_executions=total,
                successful_executions=successful,
                failed_executions=row.get('failed', 0) or 0,
                avg_execution_time_ms=float(row['avg_time']) if row.get('avg_time') else None,
                avg_risk_score=float(row['avg_risk']) if row.get('avg_risk') else None,
                success_rate=successful / total if total > 0 else None
            ))

        return trends

    def get_metric_comparison(
        self,
        schema_id: UUID,
        metric: str,
        days: int = 7
    ) -> MetricComparison:
        """
        Compare metric between current and previous period.

        Args:
            schema_id: Schema to analyze
            metric: Metric name
            days: Period length in days

        Returns:
            MetricComparison with trend
        """
        now = datetime.utcnow()
        current_start = now - timedelta(days=days)
        previous_start = current_start - timedelta(days=days)

        # Get current period stats
        current_stats = self._get_period_stats(schema_id, current_start, now)
        previous_stats = self._get_period_stats(schema_id, previous_start, current_start)

        current_value = self._extract_metric(current_stats, metric)
        previous_value = self._extract_metric(previous_stats, metric)

        change = None
        change_percentage = None
        trend = "stable"
        is_improvement = None

        if current_value is not None and previous_value is not None:
            change = current_value - previous_value
            if previous_value != 0:
                change_percentage = (change / previous_value) * 100

            # Determine trend
            if abs(change_percentage or 0) > 5:
                if change > 0:
                    trend = "up"
                else:
                    trend = "down"

            # Determine if improvement
            if metric == "success_rate":
                is_improvement = change > 0 if change else None
            else:  # execution_time, risk_score (lower is better)
                is_improvement = change < 0 if change else None

        return MetricComparison(
            metric_name=metric,
            current_value=current_value,
            previous_value=previous_value,
            change=change,
            change_percentage=change_percentage,
            trend=trend,
            is_improvement=is_improvement
        )

    def _get_period_stats(
        self,
        schema_id: UUID,
        start: datetime,
        end: datetime
    ) -> Dict[str, Any]:
        """Get stats for a specific time period."""
        query = """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE execution_status IN ('completed', 'approved')) as successful,
                AVG(execution_time_ms) as avg_time,
                AVG(risk_score) as avg_risk
            FROM csa.workflow_executions
            WHERE schema_id = %s
              AND created_at >= %s
              AND created_at < %s;
        """

        result = self.db.execute_query_dict(query, (schema_id, start, end))
        return result[0] if result else {}

    def _extract_metric(
        self,
        stats: Dict[str, Any],
        metric: str
    ) -> Optional[float]:
        """Extract metric value from stats."""
        if not stats:
            return None

        if metric == "success_rate":
            total = stats.get('total', 0) or 0
            successful = stats.get('successful', 0) or 0
            return successful / total if total > 0 else None
        elif metric == "execution_time":
            return float(stats['avg_time']) if stats.get('avg_time') else None
        elif metric == "risk_score":
            return float(stats['avg_risk']) if stats.get('avg_risk') else None

        return None

    # ========================================================================
    # STATISTICAL HELPERS
    # ========================================================================

    def _normal_cdf(self, x: float) -> float:
        """
        Approximate cumulative distribution function for standard normal.

        Uses Abramowitz and Stegun approximation.
        """
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.061405429
        p = 0.3275911

        sign = 1 if x >= 0 else -1
        x = abs(x) / math.sqrt(2)

        t = 1.0 / (1.0 + p * x)
        y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)

        return 0.5 * (1.0 + sign * y)

    def _t_cdf(self, t: float, df: float) -> float:
        """
        Approximate CDF for t-distribution.

        Uses normal approximation for large df.
        """
        if df <= 0:
            return 0.5

        if df > 100:
            # Use normal approximation for large df
            return self._normal_cdf(t)

        # Simple approximation using incomplete beta function
        x = df / (df + t * t)
        return 1 - 0.5 * self._incomplete_beta(df / 2, 0.5, x)

    def _incomplete_beta(self, a: float, b: float, x: float) -> float:
        """
        Approximate incomplete beta function.

        Simple approximation - for production use scipy.special.betainc
        """
        if x <= 0:
            return 0
        if x >= 1:
            return 1

        # Use continued fraction approximation
        # This is a simplified version
        return x ** a * (1 - x) ** b / (a + 1)

    def _welch_df(
        self,
        s1: float,
        n1: int,
        s2: float,
        n2: int
    ) -> float:
        """Calculate Welch-Satterthwaite degrees of freedom."""
        if n1 <= 1 or n2 <= 1:
            return max(1, n1 + n2 - 2)

        v1 = s1 ** 2 / n1
        v2 = s2 ** 2 / n2

        if v1 + v2 == 0:
            return max(1, n1 + n2 - 2)

        numerator = (v1 + v2) ** 2
        denominator = (v1 ** 2 / (n1 - 1)) + (v2 ** 2 / (n2 - 1))

        if denominator == 0:
            return max(1, n1 + n2 - 2)

        return numerator / denominator

    def _cohens_h(self, p1: float, p2: float) -> float:
        """Calculate Cohen's h effect size for proportions."""
        # Arcsine transformation
        phi1 = 2 * math.asin(math.sqrt(p1)) if 0 <= p1 <= 1 else 0
        phi2 = 2 * math.asin(math.sqrt(p2)) if 0 <= p2 <= 1 else 0
        return abs(phi2 - phi1)
