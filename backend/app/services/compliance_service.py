"""EngiTrace AI — Compliance Service (Phase 3)

Provides interface to execute the deterministic compliance engine against:
  1. In-memory DigitalThread instances
  2. Excel workbooks (e.g. EngiTrace_Template.xlsx)
  3. PostgreSQL database sessions
"""

from typing import Dict, Any, Optional
from datetime import datetime
import openpyxl

from backend.app.domain.models import (
    DigitalThread, Requirement, Risk, Control, Verification, Evidence, AuditLog
)
from backend.app.engine.compliance_engine import ComplianceEngine


class ComplianceService:
    """Service layer for running deterministic compliance evaluations."""

    def __init__(self):
        self.engine = ComplianceEngine()

    def evaluate_thread(self, thread: DigitalThread, evaluation_id: Optional[str] = None):
        """Evaluates an in-memory DigitalThread object."""
        return self.engine.evaluate(thread, evaluation_id=evaluation_id)

    def evaluate_database(
        self,
        db: Any,
        persist_findings: bool = False,
        evaluation_id: Optional[str] = None
    ):
        """Loads digital thread from active DB session, runs deterministic engine, and optionally persists findings."""
        thread = self.load_from_db(db)
        result = self.evaluate_thread(thread, evaluation_id=evaluation_id)

        if persist_findings and result.findings:
            from backend.app.models.db_models import DBComplianceFinding
            from backend.app.repositories.finding_repo import FindingRepository
            db_findings = []
            for f in result.findings:
                db_findings.append(DBComplianceFinding(
                    finding_id=f.finding_id,
                    target_entity_type=f.target_entity_type,
                    target_entity_id=f.target_entity_id,
                    rule_violated=f.rule_violated,
                    severity=f.severity,
                    message=f.message,
                    finding_status=f.finding_status,
                    created_date=f.created_date or datetime.utcnow(),
                    resolved_date=f.resolved_date,
                    resolution=f.resolution,
                    assigned_to=f.assigned_to
                ))
            FindingRepository.save_bulk(db, db_findings)
            db.commit()

        return result

    def load_from_excel(self, excel_path: str) -> DigitalThread:
        """Loads a DigitalThread instance from an EngiTrace Excel template."""
        wb = openpyxl.load_workbook(excel_path, data_only=True)
        thread = DigitalThread()

        # 1. Requirements
        if "Requirements" in wb.sheetnames:
            ws = wb["Requirements"]
            headers = [c.value for c in ws[1] if c.value is not None]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                d = dict(zip(headers, row))
                created_dt = self._parse_iso_date(d.get("Created_Date"))
                mod_dt = self._parse_iso_date(d.get("Last_Modified_Date"))
                thread.requirements[str(d["Req_ID"])] = Requirement(
                    req_id=str(d["Req_ID"]),
                    version=str(d.get("Version", "v1.0")),
                    description=str(d.get("Description", "")),
                    category=str(d.get("Category", "Structural_Loading")),
                    rationale=str(d.get("Rationale", "") or ""),
                    source=str(d.get("Source", "")),
                    priority=str(d.get("Priority", "Must_Have")),
                    owner=str(d.get("Owner")) if d.get("Owner") else None,
                    verification_method=str(d.get("Verification_Method", "Analysis")),
                    acceptance_criteria=str(d.get("Acceptance_Criteria", "")),
                    status=str(d.get("Status", "Draft")),
                    created_date=created_dt,
                    last_modified_date=mod_dt
                )

        # 2. Risks
        if "Risks" in wb.sheetnames:
            ws = wb["Risks"]
            headers = [c.value for c in ws[1] if c.value is not None]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                d = dict(zip(headers, row))
                pre_sev = int(d.get("Pre_Severity", 1) or 1)
                pre_like = int(d.get("Pre_Likelihood", 1) or 1)
                det = int(d.get("Detectability")) if d.get("Detectability") else None
                thread.risks[str(d["Risk_ID"])] = Risk(
                    risk_id=str(d["Risk_ID"]),
                    parent_req_id=str(d.get("Parent_Req_ID", "")),
                    failure_mode=str(d.get("Failure_Mode", "")),
                    cause=str(d.get("Cause", "")),
                    effect=str(d.get("Effect", "")),
                    pre_severity=pre_sev,
                    pre_likelihood=pre_like,
                    detectability=det,
                    risk_score=pre_sev * pre_like,
                    risk_category=str(d.get("Risk_Category", "Structural_Yielding")),
                    owner=str(d.get("Owner")) if d.get("Owner") else None,
                    status=str(d.get("Status", "Identified"))
                )

        # 3. Controls
        if "Controls" in wb.sheetnames:
            ws = wb["Controls"]
            headers = [c.value for c in ws[1] if c.value is not None]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                d = dict(zip(headers, row))
                post_sev = int(d.get("Post_Severity", 1) or 1)
                post_like = int(d.get("Post_Likelihood", 1) or 1)
                impl_dt = self._parse_iso_date(d.get("Implementation_Date"))
                thread.controls[str(d["Control_ID"])] = Control(
                    control_id=str(d["Control_ID"]),
                    parent_risk_id=str(d.get("Parent_Risk_ID", "")),
                    hierarchy_type=str(d.get("Hierarchy_Type", "Inherently_Safe_Design")),
                    description=str(d.get("Description", "")),
                    rationale=str(d.get("Rationale")) if d.get("Rationale") else None,
                    post_severity=post_sev,
                    post_likelihood=post_like,
                    residual_risk=post_sev * post_like,
                    owner=str(d.get("Owner")) if d.get("Owner") else None,
                    status=str(d.get("Status", "Proposed")),
                    implementation_date=impl_dt
                )

        # 4. Verifications
        if "Verifications" in wb.sheetnames:
            ws = wb["Verifications"]
            headers = [c.value for c in ws[1] if c.value is not None]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                d = dict(zip(headers, row))
                thread.verifications[str(d["Verif_ID"])] = Verification(
                    verif_id=str(d["Verif_ID"]),
                    target_type=str(d.get("Target_Type", "Requirement")),
                    target_req_id=str(d.get("Target_Req_ID")) if d.get("Target_Req_ID") else None,
                    target_control_id=str(d.get("Target_Control_ID")) if d.get("Target_Control_ID") else None,
                    method=str(d.get("Method", "Analysis")),
                    acceptance_crit=str(d.get("Acceptance_Crit", "")),
                    reviewer=str(d.get("Reviewer")) if d.get("Reviewer") else None,
                    status=str(d.get("Status", "Planned"))
                )

        # 5. Evidence
        if "Evidence" in wb.sheetnames:
            ws = wb["Evidence"]
            headers = [c.value for c in ws[1] if c.value is not None]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or not row[0]:
                    continue
                d = dict(zip(headers, row))
                gen_dt = self._parse_iso_date(d.get("Date_Generated"))
                thread.evidence[str(d["Evid_ID"])] = Evidence(
                    evid_id=str(d["Evid_ID"]),
                    parent_verif_id=str(d.get("Parent_Verif_ID", "")),
                    evidence_type=str(d.get("Evidence_Type", "Simulation_Report")),
                    file_name=str(d.get("File_Name", "")),
                    artifact_ref=str(d.get("Artifact_Ref", "")),
                    hash=str(d.get("Hash")) if d.get("Hash") else None,
                    result_value=str(d.get("Result_Value")) if d.get("Result_Value") else None,
                    date_generated=gen_dt,
                    approval_status=str(d.get("Approval_Status", "Uploaded"))
                )

        return thread

    def load_from_db(self, session: Any) -> DigitalThread:
        """Loads a DigitalThread instance directly from active PostgreSQL tables."""
        from sqlalchemy import text
        thread = DigitalThread()

        # Load requirements
        for row in session.execute(text("SELECT * FROM requirements")).mappings():
            thread.requirements[row["req_id"]] = Requirement(
                req_id=row["req_id"],
                version=row["version"],
                description=row["description"],
                category=row["category"],
                rationale=row["rationale"],
                source=row["source"],
                priority=row["priority"],
                owner=row["owner"],
                verification_method=row["verification_method"],
                acceptance_criteria=row["acceptance_criteria"],
                status=row["status"],
                created_date=row["created_date"],
                last_modified_date=row["last_modified_date"]
            )

        # Load risks
        for row in session.execute(text("SELECT * FROM risks")).mappings():
            thread.risks[row["risk_id"]] = Risk(
                risk_id=row["risk_id"],
                parent_req_id=row["parent_req_id"],
                failure_mode=row["failure_mode"],
                cause=row["cause"],
                effect=row["effect"],
                pre_severity=row["pre_severity"],
                pre_likelihood=row["pre_likelihood"],
                detectability=row["detectability"],
                risk_score=row["risk_score"],
                risk_category=row["risk_category"],
                owner=row["owner"],
                status=row["status"]
            )

        # Load controls
        for row in session.execute(text("SELECT * FROM controls")).mappings():
            thread.controls[row["control_id"]] = Control(
                control_id=row["control_id"],
                parent_risk_id=row["parent_risk_id"],
                hierarchy_type=row["hierarchy_type"],
                description=row["description"],
                rationale=row["rationale"],
                post_severity=row["post_severity"],
                post_likelihood=row["post_likelihood"],
                residual_risk=row["residual_risk"],
                owner=row["owner"],
                status=row["status"],
                implementation_date=row["implementation_date"]
            )

        # Load verifications
        for row in session.execute(text("SELECT * FROM verifications")).mappings():
            thread.verifications[row["verif_id"]] = Verification(
                verif_id=row["verif_id"],
                target_type=row["target_type"],
                target_req_id=row["target_req_id"],
                target_control_id=row["target_control_id"],
                method=row["method"],
                acceptance_crit=row["acceptance_crit"],
                reviewer=row["reviewer"],
                status=row["status"]
            )

        # Load evidence
        for row in session.execute(text("SELECT * FROM evidence")).mappings():
            thread.evidence[row["evid_id"]] = Evidence(
                evid_id=row["evid_id"],
                parent_verif_id=row["parent_verif_id"],
                evidence_type=row["evidence_type"],
                file_name=row["file_name"],
                artifact_ref=row["artifact_ref"],
                hash=row["hash"],
                result_value=row["result_value"],
                date_generated=row["date_generated"],
                approval_status=row["approval_status"]
            )

        # Load audit logs
        for row in session.execute(text("SELECT * FROM audit_logs")).mappings():
            thread.audit_logs.append(AuditLog(
                log_id=row["log_id"],
                entity_type=row["entity_type"],
                entity_id=row["entity_id"],
                action=row["action"],
                field_name=row["field_name"],
                previous_value=row["previous_value"],
                new_value=row["new_value"],
                user_id=row["user_id"],
                reason=row["reason"],
                timestamp=row["timestamp"]
            ))

        return thread

    @staticmethod
    def _parse_iso_date(val: Any) -> Optional[datetime]:
        """Safely parses ISO 8601 timestamps or datetime objects to UTC timezone-aware datetimes."""
        from datetime import timezone
        if isinstance(val, datetime):
            if val.tzinfo is None:
                return val.replace(tzinfo=timezone.utc)
            return val
        if isinstance(val, str) and val.strip():
            try:
                # Handle 'Z' suffix
                clean_str = val.replace("Z", "+00:00")
                dt = datetime.fromisoformat(clean_str)
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            except Exception:
                return None
        return None
