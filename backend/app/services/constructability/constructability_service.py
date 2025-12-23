"""
Constructability Service.

Phase 4 Sprint 2: The Constructability Agent (Geometric Logic)

This service provides:
- Automatic constructability audits when designs are generated
- Integration with workflow execution system
- Red Flag Report management
- Mitigation plan generation
- Alert system for critical issues
"""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.config import settings
from app.core.database import get_db
from app.engines.constructability import (
    analyze_constructability,
    analyze_rebar_congestion,
    analyze_formwork_complexity,
    generate_red_flag_report,
    generate_constructability_plan,
)
from app.schemas.constructability.models import (
    ConstructabilityAuditRequest,
    ConstructabilityAuditResponse,
    ConstructabilityAnalysisResult,
    RedFlagReport,
    ConstructabilityPlan,
    RedFlagSeverity,
)


class ConstructabilityService:
    """
    Service for managing constructability audits and reports.

    This service:
    1. Automatically audits design outputs from workflow executions
    2. Generates Red Flag Reports for critical issues
    3. Creates mitigation plans
    4. Stores audit results for tracking
    5. Sends alerts for critical findings
    """

    def __init__(self):
        """Initialize the constructability service."""
        self.supabase = get_db()

    # =========================================================================
    # CORE AUDIT FUNCTIONS
    # =========================================================================

    def run_audit(
        self,
        request: ConstructabilityAuditRequest
    ) -> ConstructabilityAuditResponse:
        """
        Run a complete constructability audit.

        Args:
            request: Audit request with design data or execution ID

        Returns:
            Complete audit response with analysis and Red Flag Report
        """
        started_at = datetime.utcnow()
        audit_id = f"CA-{uuid.uuid4().hex[:8].upper()}"
        errors: List[str] = []

        try:
            # Get design data
            if request.execution_id:
                design_data = self._get_execution_output(request.execution_id)
                if not design_data:
                    errors.append(f"Execution {request.execution_id} not found or has no output")
                    return ConstructabilityAuditResponse(
                        audit_id=audit_id,
                        status="failed",
                        errors=errors,
                        started_at=started_at.isoformat(),
                        completed_at=datetime.utcnow().isoformat(),
                        duration_seconds=(datetime.utcnow() - started_at).total_seconds(),
                    )
            else:
                design_data = request.design_data

            # Build analysis input
            analysis_input = {
                "project_id": str(request.project_id) if request.project_id else None,
                "execution_id": str(request.execution_id) if request.execution_id else None,
                "design_outputs": design_data,
                "include_cost_analysis": request.include_cost_analysis,
                "include_schedule_analysis": request.include_schedule_analysis,
                "analysis_depth": (
                    "quick" if request.audit_type == "quick"
                    else "detailed" if request.audit_type == "full"
                    else "standard"
                ),
            }

            # Run appropriate analysis based on audit type
            if request.audit_type == "rebar_only":
                # Only rebar congestion analysis
                members = self._extract_members(design_data)
                analysis_result = self._run_rebar_only_audit(members)
            elif request.audit_type == "formwork_only":
                # Only formwork complexity analysis
                members = self._extract_members(design_data)
                analysis_result = self._run_formwork_only_audit(members)
            else:
                # Full analysis
                analysis_result = analyze_constructability(analysis_input)

            # Apply custom thresholds if provided
            if request.congestion_threshold is not None:
                analysis_result = self._apply_congestion_threshold(
                    analysis_result, request.congestion_threshold
                )
            if request.complexity_threshold is not None:
                analysis_result = self._apply_complexity_threshold(
                    analysis_result, request.complexity_threshold
                )

            # Generate Red Flag Report
            report_input = {
                **analysis_result,
                "project_id": str(request.project_id) if request.project_id else None,
                "execution_id": str(request.execution_id) if request.execution_id else None,
            }
            red_flag_report = generate_red_flag_report(report_input)

            # Store audit results
            self._store_audit_result(
                audit_id=audit_id,
                request=request,
                analysis_result=analysis_result,
                red_flag_report=red_flag_report,
            )

            # Send alerts for critical issues
            if red_flag_report.get("critical_count", 0) > 0:
                self._send_critical_alerts(audit_id, red_flag_report, request.requested_by)

            completed_at = datetime.utcnow()

            return ConstructabilityAuditResponse(
                audit_id=audit_id,
                status="completed",
                analysis_result=ConstructabilityAnalysisResult(**analysis_result),
                red_flag_report=RedFlagReport(**red_flag_report),
                errors=errors,
                started_at=started_at.isoformat(),
                completed_at=completed_at.isoformat(),
                duration_seconds=(completed_at - started_at).total_seconds(),
            )

        except Exception as e:
            errors.append(f"Audit failed: {str(e)}")
            return ConstructabilityAuditResponse(
                audit_id=audit_id,
                status="failed",
                errors=errors,
                started_at=started_at.isoformat(),
                completed_at=datetime.utcnow().isoformat(),
                duration_seconds=(datetime.utcnow() - started_at).total_seconds(),
            )

    def audit_execution(
        self,
        execution_id: UUID,
        requested_by: str,
        audit_type: str = "full"
    ) -> ConstructabilityAuditResponse:
        """
        Convenience method to audit a workflow execution by ID.

        Args:
            execution_id: ID of the workflow execution
            requested_by: User requesting the audit
            audit_type: Type of audit (full, quick, rebar_only, formwork_only)

        Returns:
            Audit response
        """
        request = ConstructabilityAuditRequest(
            execution_id=execution_id,
            audit_type=audit_type,
            requested_by=requested_by,
        )
        return self.run_audit(request)

    def audit_design_data(
        self,
        design_data: Dict[str, Any],
        requested_by: str,
        project_id: Optional[UUID] = None,
        audit_type: str = "full"
    ) -> ConstructabilityAuditResponse:
        """
        Convenience method to audit direct design data.

        Args:
            design_data: Design output data to audit
            requested_by: User requesting the audit
            project_id: Optional project ID
            audit_type: Type of audit

        Returns:
            Audit response
        """
        request = ConstructabilityAuditRequest(
            design_data=design_data,
            audit_type=audit_type,
            requested_by=requested_by,
            project_id=project_id,
        )
        return self.run_audit(request)

    # =========================================================================
    # SPECIALIZED ANALYSIS FUNCTIONS
    # =========================================================================

    def analyze_member_congestion(
        self,
        member_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze rebar congestion for a single member.

        Args:
            member_data: Member geometry and reinforcement data

        Returns:
            Congestion analysis result
        """
        return analyze_rebar_congestion(member_data)

    def analyze_member_formwork(
        self,
        member_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze formwork complexity for a single member.

        Args:
            member_data: Member geometry and features

        Returns:
            Formwork complexity result
        """
        return analyze_formwork_complexity(member_data)

    def generate_mitigation_plan(
        self,
        analysis_result: Dict[str, Any],
        project_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Generate a mitigation plan from analysis results.

        Args:
            analysis_result: Constructability analysis result
            project_id: Optional project ID

        Returns:
            Constructability plan with mitigation strategies
        """
        plan_input = {
            **analysis_result,
            "project_id": str(project_id) if project_id else None,
        }
        return generate_constructability_plan(plan_input)

    # =========================================================================
    # RETRIEVAL FUNCTIONS
    # =========================================================================

    def get_audit(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a stored audit result by ID.

        Args:
            audit_id: Audit identifier

        Returns:
            Audit record or None if not found
        """
        try:
            result = self.supabase.table("constructability_audits") \
                .select("*") \
                .eq("audit_id", audit_id) \
                .single() \
                .execute()
            return result.data if result.data else None
        except Exception:
            return None

    def get_audits_for_project(
        self,
        project_id: UUID,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all audits for a project.

        Args:
            project_id: Project identifier
            limit: Maximum number of audits to return

        Returns:
            List of audit records
        """
        try:
            result = self.supabase.table("constructability_audits") \
                .select("*") \
                .eq("project_id", str(project_id)) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            return result.data or []
        except Exception:
            return []

    def get_audits_for_execution(
        self,
        execution_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get all audits for a workflow execution.

        Args:
            execution_id: Execution identifier

        Returns:
            List of audit records
        """
        try:
            result = self.supabase.table("constructability_audits") \
                .select("*") \
                .eq("execution_id", str(execution_id)) \
                .order("created_at", desc=True) \
                .execute()
            return result.data or []
        except Exception:
            return []

    def get_red_flag_report(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the Red Flag Report for an audit.

        Args:
            audit_id: Audit identifier

        Returns:
            Red Flag Report or None
        """
        audit = self.get_audit(audit_id)
        if audit:
            return audit.get("red_flag_report")
        return None

    def get_open_flags(
        self,
        project_id: Optional[UUID] = None,
        severity: Optional[RedFlagSeverity] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all open (unresolved) red flags.

        Args:
            project_id: Filter by project
            severity: Filter by severity

        Returns:
            List of open flags
        """
        try:
            query = self.supabase.table("constructability_flags") \
                .select("*") \
                .eq("status", "open")

            if project_id:
                query = query.eq("project_id", str(project_id))

            if severity:
                query = query.eq("severity", severity.value)

            result = query.order("created_at", desc=True).execute()
            return result.data or []
        except Exception:
            return []

    # =========================================================================
    # FLAG MANAGEMENT
    # =========================================================================

    def resolve_flag(
        self,
        flag_id: str,
        resolution_notes: str,
        resolved_by: str
    ) -> bool:
        """
        Mark a red flag as resolved.

        Args:
            flag_id: Flag identifier
            resolution_notes: Notes on how the flag was resolved
            resolved_by: User who resolved the flag

        Returns:
            True if successful
        """
        try:
            self.supabase.table("constructability_flags") \
                .update({
                    "status": "resolved",
                    "resolution_notes": resolution_notes,
                    "resolved_by": resolved_by,
                    "resolved_at": datetime.utcnow().isoformat(),
                }) \
                .eq("flag_id", flag_id) \
                .execute()
            return True
        except Exception:
            return False

    def accept_flag(
        self,
        flag_id: str,
        acceptance_notes: str,
        accepted_by: str
    ) -> bool:
        """
        Accept a red flag (acknowledge risk without resolving).

        Args:
            flag_id: Flag identifier
            acceptance_notes: Notes on why the flag is accepted
            accepted_by: User who accepted the flag

        Returns:
            True if successful
        """
        try:
            self.supabase.table("constructability_flags") \
                .update({
                    "status": "accepted",
                    "resolution_notes": acceptance_notes,
                    "resolved_by": accepted_by,
                    "resolved_at": datetime.utcnow().isoformat(),
                }) \
                .eq("flag_id", flag_id) \
                .execute()
            return True
        except Exception:
            return False

    # =========================================================================
    # STATISTICS
    # =========================================================================

    def get_statistics(
        self,
        project_id: Optional[UUID] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get constructability audit statistics.

        Args:
            project_id: Filter by project
            days: Number of days to include

        Returns:
            Statistics dictionary
        """
        try:
            # Get audits in time range
            from datetime import timedelta
            cutoff = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff = cutoff - timedelta(days=days)

            query = self.supabase.table("constructability_audits") \
                .select("*") \
                .gte("created_at", cutoff.isoformat())

            if project_id:
                query = query.eq("project_id", str(project_id))

            result = query.execute()
            audits = result.data or []

            # Calculate statistics
            total_audits = len(audits)
            passed = sum(1 for a in audits if a.get("status") == "completed" and
                        a.get("red_flag_report", {}).get("overall_status") == "pass")
            conditional = sum(1 for a in audits if a.get("red_flag_report", {}).get("overall_status") == "conditional_pass")
            failed = sum(1 for a in audits if a.get("red_flag_report", {}).get("overall_status") == "fail")

            # Count flags
            total_flags = sum(a.get("red_flag_report", {}).get("total_flags", 0) for a in audits)
            critical_flags = sum(a.get("red_flag_report", {}).get("critical_count", 0) for a in audits)
            major_flags = sum(a.get("red_flag_report", {}).get("major_count", 0) for a in audits)

            # Average scores
            if audits:
                avg_congestion = sum(a.get("analysis_result", {}).get("rebar_congestion_score", 0) for a in audits) / total_audits
                avg_formwork = sum(a.get("analysis_result", {}).get("formwork_complexity_score", 0) for a in audits) / total_audits
                avg_risk = sum(a.get("analysis_result", {}).get("overall_risk_score", 0) for a in audits) / total_audits
            else:
                avg_congestion = 0
                avg_formwork = 0
                avg_risk = 0

            return {
                "period_days": days,
                "total_audits": total_audits,
                "passed": passed,
                "conditional_pass": conditional,
                "failed": failed,
                "pass_rate": round(passed / total_audits * 100, 1) if total_audits > 0 else 0,
                "total_flags": total_flags,
                "critical_flags": critical_flags,
                "major_flags": major_flags,
                "average_congestion_score": round(avg_congestion, 3),
                "average_formwork_score": round(avg_formwork, 3),
                "average_risk_score": round(avg_risk, 3),
            }
        except Exception as e:
            return {"error": str(e)}

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_execution_output(self, execution_id: UUID) -> Optional[Dict[str, Any]]:
        """Get output data from a workflow execution."""
        try:
            result = self.supabase.table("workflow_executions") \
                .select("output_data") \
                .eq("id", str(execution_id)) \
                .single() \
                .execute()
            if result.data:
                return result.data.get("output_data")
            return None
        except Exception:
            return None

    def _extract_members(self, design_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract member data from design outputs."""
        # Import here to avoid circular dependency
        from app.engines.constructability.constructability_analyzer import extract_members_from_design
        return extract_members_from_design(design_data)

    def _run_rebar_only_audit(self, members: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run rebar-only analysis on members."""
        results = []
        issues = []

        for member in members:
            try:
                result = analyze_rebar_congestion({
                    "member_type": member.get("member_type", "beam"),
                    "member_id": member.get("member_id", "UNKNOWN"),
                    "width": member.get("width", 300),
                    "depth": member.get("depth", 600),
                    "main_bar_diameter": member.get("main_bar_diameter", 16),
                    "main_bar_count": member.get("main_bar_count", 4),
                    "clear_cover": member.get("clear_cover", 40),
                    "concrete_grade": member.get("concrete_grade", "M25"),
                })
                results.append(result)
            except Exception as e:
                issues.append({
                    "issue_id": f"ERR-{uuid.uuid4().hex[:8]}",
                    "severity": "warning",
                    "category": "analysis_error",
                    "title": f"Analysis failed for {member.get('member_id', 'UNKNOWN')}",
                    "description": str(e),
                })

        avg_score = sum(r.get("congestion_score", 0) for r in results) / len(results) if results else 0

        return {
            "overall_risk_score": avg_score,
            "risk_level": "low" if avg_score < 0.25 else "medium" if avg_score < 0.5 else "high" if avg_score < 0.75 else "critical",
            "is_constructable": avg_score < 0.75,
            "requires_modifications": avg_score > 0.5,
            "rebar_congestion_score": avg_score,
            "formwork_complexity_score": 0,
            "access_constraint_score": 0,
            "sequencing_complexity_score": 0,
            "congestion_results": results,
            "formwork_results": [],
            "issues": issues,
            "members_analyzed": len(members),
            "analysis_depth": "rebar_only",
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    def _run_formwork_only_audit(self, members: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run formwork-only analysis on members."""
        results = []
        issues = []

        for member in members:
            try:
                result = analyze_formwork_complexity({
                    "member_type": member.get("member_type", "beam"),
                    "member_id": member.get("member_id", "UNKNOWN"),
                    "length": member.get("length", 5000),
                    "width": member.get("width", 300),
                    "depth": member.get("depth", 600),
                })
                results.append(result)
            except Exception as e:
                issues.append({
                    "issue_id": f"ERR-{uuid.uuid4().hex[:8]}",
                    "severity": "warning",
                    "category": "analysis_error",
                    "title": f"Analysis failed for {member.get('member_id', 'UNKNOWN')}",
                    "description": str(e),
                })

        avg_score = sum(r.get("complexity_score", 0) for r in results) / len(results) if results else 0

        return {
            "overall_risk_score": avg_score,
            "risk_level": "low" if avg_score < 0.25 else "medium" if avg_score < 0.5 else "high" if avg_score < 0.75 else "critical",
            "is_constructable": avg_score < 0.75,
            "requires_modifications": avg_score > 0.5,
            "rebar_congestion_score": 0,
            "formwork_complexity_score": avg_score,
            "access_constraint_score": 0,
            "sequencing_complexity_score": 0,
            "congestion_results": [],
            "formwork_results": results,
            "issues": issues,
            "members_analyzed": len(members),
            "analysis_depth": "formwork_only",
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    def _apply_congestion_threshold(
        self,
        result: Dict[str, Any],
        threshold: float
    ) -> Dict[str, Any]:
        """Apply custom congestion threshold to results."""
        # Recalculate issues based on new threshold
        for congestion in result.get("congestion_results", []):
            if congestion.get("congestion_score", 0) > threshold:
                congestion["flagged"] = True
        return result

    def _apply_complexity_threshold(
        self,
        result: Dict[str, Any],
        threshold: float
    ) -> Dict[str, Any]:
        """Apply custom complexity threshold to results."""
        for formwork in result.get("formwork_results", []):
            if formwork.get("complexity_score", 0) > threshold:
                formwork["flagged"] = True
        return result

    def _store_audit_result(
        self,
        audit_id: str,
        request: ConstructabilityAuditRequest,
        analysis_result: Dict[str, Any],
        red_flag_report: Dict[str, Any]
    ) -> None:
        """Store audit result in database."""
        try:
            self.supabase.table("constructability_audits").insert({
                "audit_id": audit_id,
                "project_id": str(request.project_id) if request.project_id else None,
                "execution_id": str(request.execution_id) if request.execution_id else None,
                "audit_type": request.audit_type,
                "requested_by": request.requested_by,
                "status": "completed",
                "analysis_result": analysis_result,
                "red_flag_report": red_flag_report,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()

            # Also store individual flags for easier querying
            for flag in red_flag_report.get("flags", []):
                self.supabase.table("constructability_flags").insert({
                    "flag_id": flag.get("flag_id"),
                    "audit_id": audit_id,
                    "project_id": str(request.project_id) if request.project_id else None,
                    "severity": flag.get("severity"),
                    "category": flag.get("category"),
                    "member_id": flag.get("member_id"),
                    "title": flag.get("title"),
                    "description": flag.get("description"),
                    "status": "open",
                    "created_at": datetime.utcnow().isoformat(),
                }).execute()

        except Exception as e:
            # Log but don't fail the audit
            print(f"Warning: Failed to store audit result: {e}")

    def _send_critical_alerts(
        self,
        audit_id: str,
        report: Dict[str, Any],
        requested_by: str
    ) -> None:
        """Send alerts for critical issues."""
        try:
            # Create notification record
            self.supabase.table("notifications").insert({
                "id": str(uuid.uuid4()),
                "user_id": requested_by,
                "notification_type": "constructability_critical",
                "title": "Critical Constructability Issues Detected",
                "message": (
                    f"Audit {audit_id} found {report.get('critical_count', 0)} critical issues. "
                    f"Review the Red Flag Report immediately."
                ),
                "data": {
                    "audit_id": audit_id,
                    "critical_count": report.get("critical_count", 0),
                    "major_count": report.get("major_count", 0),
                },
                "is_read": False,
                "created_at": datetime.utcnow().isoformat(),
            }).execute()
        except Exception as e:
            print(f"Warning: Failed to send critical alert: {e}")
