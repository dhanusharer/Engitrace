"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-24 17:00:00.000000

Physical PostgreSQL schema implementation for EngiTrace AI.
Encompasses the 7 locked tables:
  1. requirements
  2. risks
  3. controls
  4. verifications
  5. evidence
  6. compliance_findings
  7. audit_logs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. REQUIREMENTS TABLE
    # -------------------------------------------------------------------------
    op.create_table(
        'requirements',
        sa.Column('req_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('version', sa.VARCHAR(length=16), server_default='v1.0', nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.VARCHAR(length=32), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('source', sa.VARCHAR(length=128), nullable=False),
        sa.Column('priority', sa.VARCHAR(length=16), nullable=False),
        sa.Column('owner', sa.VARCHAR(length=64), nullable=True),
        sa.Column('verification_method', sa.VARCHAR(length=32), nullable=False),
        sa.Column('acceptance_criteria', sa.Text(), nullable=False),
        sa.Column('status', sa.VARCHAR(length=24), server_default='Draft', nullable=False),
        sa.Column('created_date', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_modified_date', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('req_id', name='pk_requirements'),
        sa.CheckConstraint("req_id ~ '^REQ-[A-Z]{3}-[A-Z]{3}-[0-9]{3,4}$'", name='chk_req_id_format'),
        sa.CheckConstraint(
            "category IN ('Structural_Loading', 'Aerodynamic_Performance', 'Fatigue_Life', "
            "'Material_Integrity', 'Geometric_Constraints', 'Manufacturing_Quality', 'Environmental_Survivability')",
            name='chk_req_category'
        ),
        sa.CheckConstraint(
            "priority IN ('Must_Have', 'Should_Have', 'Could_Have', 'Won_t_Have')",
            name='chk_req_priority'
        ),
        sa.CheckConstraint(
            "verification_method IN ('Analysis', 'Test', 'Inspection', 'Demonstration')",
            name='chk_req_verification_method'
        ),
        sa.CheckConstraint(
            "status IN ('Draft', 'Under_Review', 'Approved', 'Rejected', 'Retired')",
            name='chk_req_status'
        ),
        sa.CheckConstraint("char_length(description) >= 20", name='chk_req_description_len'),
        sa.CheckConstraint("char_length(rationale) >= 15", name='chk_req_rationale_len'),
        sa.CheckConstraint("last_modified_date >= created_date", name='chk_req_dates')
    )
    op.create_index('idx_requirements_category', 'requirements', ['category'])
    op.create_index('idx_requirements_status', 'requirements', ['status'])
    op.create_index('idx_requirements_last_modified', 'requirements', ['last_modified_date'])

    # Requirement timestamp auto-update trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_update_last_modified_date()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.last_modified_date = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_requirements_last_modified
        BEFORE UPDATE ON requirements
        FOR EACH ROW
        EXECUTE FUNCTION fn_update_last_modified_date();
    """)

    # -------------------------------------------------------------------------
    # 2. RISKS TABLE
    # -------------------------------------------------------------------------
    op.create_table(
        'risks',
        sa.Column('risk_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('parent_req_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('failure_mode', sa.Text(), nullable=False),
        sa.Column('cause', sa.Text(), nullable=False),
        sa.Column('effect', sa.Text(), nullable=False),
        sa.Column('pre_severity', sa.Integer(), nullable=False),
        sa.Column('pre_likelihood', sa.Integer(), nullable=False),
        sa.Column('detectability', sa.Integer(), nullable=True),
        sa.Column(
            'risk_score',
            sa.Integer(),
            sa.Computed('pre_severity * pre_likelihood', persisted=True),
            nullable=False
        ),
        sa.Column('risk_category', sa.VARCHAR(length=32), nullable=False),
        sa.Column('owner', sa.VARCHAR(length=64), nullable=True),
        sa.Column('status', sa.VARCHAR(length=24), server_default='Identified', nullable=False),
        sa.PrimaryKeyConstraint('risk_id', name='pk_risks'),
        sa.ForeignKeyConstraint(
            ['parent_req_id'], ['requirements.req_id'],
            name='fk_risks_parent_req',
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.CheckConstraint("risk_id ~ '^RSK-[A-Z]{3}-[0-9]{3,4}$'", name='chk_risk_id_format'),
        sa.CheckConstraint("pre_severity BETWEEN 1 AND 5", name='chk_risk_pre_severity'),
        sa.CheckConstraint("pre_likelihood BETWEEN 1 AND 5", name='chk_risk_pre_likelihood'),
        sa.CheckConstraint("detectability IS NULL OR detectability BETWEEN 1 AND 5", name='chk_risk_detectability'),
        sa.CheckConstraint(
            "risk_category IN ('Aerodynamic_Instability', 'Structural_Yielding', 'Fatigue_Delamination', "
            "'Adhesive_Debonding', 'Buckling_Instability', 'Environmental_Damage', 'Manufacturing_Defect')",
            name='chk_risk_category'
        ),
        sa.CheckConstraint(
            "status IN ('Identified', 'Under_Assessment', 'Mitigated', 'Accepted', 'Closed')",
            name='chk_risk_status'
        )
    )
    op.create_index('idx_risks_parent_req', 'risks', ['parent_req_id'])
    op.create_index('idx_risks_score', 'risks', ['risk_score'])

    # -------------------------------------------------------------------------
    # 3. CONTROLS TABLE
    # -------------------------------------------------------------------------
    op.create_table(
        'controls',
        sa.Column('control_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('parent_risk_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('hierarchy_type', sa.VARCHAR(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('post_severity', sa.Integer(), nullable=False),
        sa.Column('post_likelihood', sa.Integer(), nullable=False),
        sa.Column(
            'residual_risk',
            sa.Integer(),
            sa.Computed('post_severity * post_likelihood', persisted=True),
            nullable=False
        ),
        sa.Column('owner', sa.VARCHAR(length=64), nullable=True),
        sa.Column('status', sa.VARCHAR(length=24), server_default='Proposed', nullable=False),
        sa.Column('implementation_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('control_id', name='pk_controls'),
        sa.ForeignKeyConstraint(
            ['parent_risk_id'], ['risks.risk_id'],
            name='fk_controls_parent_risk',
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.CheckConstraint("control_id ~ '^CTRL-[A-Z]{3}-[0-9]{3,4}$'", name='chk_control_id_format'),
        sa.CheckConstraint(
            "hierarchy_type IN ('Inherently_Safe_Design', 'Safeguarding', 'Information_for_Use')",
            name='chk_control_hierarchy'
        ),
        sa.CheckConstraint("post_severity BETWEEN 1 AND 5", name='chk_control_post_severity'),
        sa.CheckConstraint("post_likelihood BETWEEN 1 AND 5", name='chk_control_post_likelihood'),
        sa.CheckConstraint(
            "status IN ('Proposed', 'Approved', 'Implemented', 'Verified', 'Deprecated')",
            name='chk_control_status'
        ),
        sa.CheckConstraint("char_length(description) >= 15", name='chk_control_description_len')
    )
    op.create_index('idx_controls_parent_risk', 'controls', ['parent_risk_id'])
    op.create_index('idx_controls_hierarchy', 'controls', ['hierarchy_type'])

    # -------------------------------------------------------------------------
    # 4. VERIFICATIONS TABLE
    # -------------------------------------------------------------------------
    op.create_table(
        'verifications',
        sa.Column('verif_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('target_type', sa.VARCHAR(length=16), nullable=False),
        sa.Column('target_req_id', sa.VARCHAR(length=32), nullable=True),
        sa.Column('target_control_id', sa.VARCHAR(length=32), nullable=True),
        sa.Column('method', sa.VARCHAR(length=32), nullable=False),
        sa.Column('acceptance_crit', sa.Text(), nullable=False),
        sa.Column('reviewer', sa.VARCHAR(length=64), nullable=True),
        sa.Column('status', sa.VARCHAR(length=24), server_default='Planned', nullable=False),
        sa.PrimaryKeyConstraint('verif_id', name='pk_verifications'),
        sa.ForeignKeyConstraint(
            ['target_req_id'], ['requirements.req_id'],
            name='fk_verifications_target_req',
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.ForeignKeyConstraint(
            ['target_control_id'], ['controls.control_id'],
            name='fk_verifications_target_control',
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.CheckConstraint("verif_id ~ '^VRF-[A-Z]{3}-[0-9]{3,4}$'", name='chk_verif_id_format'),
        sa.CheckConstraint("target_type IN ('Requirement', 'Control')", name='chk_verif_target_type'),
        sa.CheckConstraint("method IN ('Analysis', 'Test', 'Inspection', 'Demonstration')", name='chk_verif_method'),
        sa.CheckConstraint("status IN ('Planned', 'In_Progress', 'Passed', 'Failed', 'Blocked')", name='chk_verif_status'),
        sa.CheckConstraint("char_length(acceptance_crit) >= 15", name='chk_verif_acceptance_crit_len'),
        sa.CheckConstraint(
            "(target_req_id IS NOT NULL AND target_control_id IS NULL) OR "
            "(target_req_id IS NULL AND target_control_id IS NOT NULL)",
            name='chk_verif_single_target'
        ),
        sa.CheckConstraint(
            "(target_type = 'Requirement' AND target_req_id IS NOT NULL) OR "
            "(target_type = 'Control' AND target_control_id IS NOT NULL)",
            name='chk_verif_target_consistency'
        )
    )
    op.create_index('idx_verifications_target_req', 'verifications', ['target_req_id'])
    op.create_index('idx_verifications_target_ctrl', 'verifications', ['target_control_id'])
    op.create_index('idx_verifications_status', 'verifications', ['status'])

    # -------------------------------------------------------------------------
    # 5. EVIDENCE TABLE
    # -------------------------------------------------------------------------
    op.create_table(
        'evidence',
        sa.Column('evid_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('parent_verif_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('evidence_type', sa.VARCHAR(length=32), nullable=False),
        sa.Column('file_name', sa.VARCHAR(length=255), nullable=False),
        sa.Column('artifact_ref', sa.VARCHAR(length=512), nullable=False),
        sa.Column('hash', sa.VARCHAR(length=64), nullable=True),
        sa.Column('result_value', sa.Text(), nullable=True),
        sa.Column('date_generated', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('approval_status', sa.VARCHAR(length=24), server_default='Uploaded', nullable=False),
        sa.PrimaryKeyConstraint('evid_id', name='pk_evidence'),
        sa.ForeignKeyConstraint(
            ['parent_verif_id'], ['verifications.verif_id'],
            name='fk_evidence_parent_verif',
            onupdate='CASCADE', ondelete='RESTRICT'
        ),
        sa.CheckConstraint("evid_id ~ '^EVD-[A-Z]{3}-[0-9]{3,4}$'", name='chk_evid_id_format'),
        sa.CheckConstraint(
            "evidence_type IN ('Simulation_Report', 'Test_Data_Log', 'UT_Scan', "
            "'Material_Certificate', 'Visual_Inspection_Log', 'Calibration_Record')",
            name='chk_evid_type'
        ),
        sa.CheckConstraint(
            "approval_status IN ('Uploaded', 'Under_Review', 'Approved', 'Rejected', 'Superseded')",
            name='chk_evid_approval_status'
        ),
        sa.CheckConstraint("char_length(trim(artifact_ref)) > 0", name='chk_evid_artifact_ref_nonempty'),
        sa.CheckConstraint("hash IS NULL OR hash ~ '^[a-fA-F0-9]{64}$'", name='chk_evid_hash_format')
    )
    op.create_index('idx_evidence_parent_verif', 'evidence', ['parent_verif_id'])
    op.create_index('idx_evidence_date', 'evidence', ['date_generated'])
    op.create_index('idx_evidence_type', 'evidence', ['evidence_type'])

    # -------------------------------------------------------------------------
    # 6. COMPLIANCE FINDINGS TABLE
    # -------------------------------------------------------------------------
    op.create_table(
        'compliance_findings',
        sa.Column('finding_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('target_entity_type', sa.VARCHAR(length=32), nullable=False),
        sa.Column('target_entity_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('rule_violated', sa.VARCHAR(length=64), nullable=False),
        sa.Column('severity', sa.VARCHAR(length=16), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('finding_status', sa.VARCHAR(length=24), server_default='Open', nullable=False),
        sa.Column('created_date', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('resolved_date', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('assigned_to', sa.VARCHAR(length=64), nullable=True),
        sa.PrimaryKeyConstraint('finding_id', name='pk_compliance_findings'),
        sa.CheckConstraint("finding_id ~ '^CMP-[A-Z]{3}-[0-9]{3,4}$'", name='chk_finding_id_format'),
        sa.CheckConstraint(
            "target_entity_type IN ('Requirement', 'Risk', 'Control', 'Verification', 'Evidence', 'Subsystem')",
            name='chk_finding_target_entity_type'
        ),
        sa.CheckConstraint("severity IN ('ERROR', 'WARNING', 'INFO')", name='chk_finding_severity'),
        sa.CheckConstraint(
            "finding_status IN ('Open', 'Under_Investigation', 'Resolved', 'Waived')",
            name='chk_finding_status'
        ),
        sa.CheckConstraint("resolved_date IS NULL OR resolved_date >= created_date", name='chk_finding_dates'),
        sa.CheckConstraint("char_length(message) >= 15", name='chk_finding_message_len')
    )
    op.create_index('idx_findings_target', 'compliance_findings', ['target_entity_type', 'target_entity_id'])
    op.create_index('idx_findings_severity', 'compliance_findings', ['severity'])
    op.create_index('idx_findings_status', 'compliance_findings', ['finding_status'])

    # -------------------------------------------------------------------------
    # 7. AUDIT LOGS TABLE
    # -------------------------------------------------------------------------
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('entity_type', sa.VARCHAR(length=32), nullable=False),
        sa.Column('entity_id', sa.VARCHAR(length=32), nullable=False),
        sa.Column('action', sa.VARCHAR(length=24), nullable=False),
        sa.Column('field_name', sa.VARCHAR(length=64), nullable=True),
        sa.Column('previous_value', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('new_value', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('user_id', sa.VARCHAR(length=64), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('log_id', name='pk_audit_logs'),
        sa.CheckConstraint("log_id ~ '^LOG-[0-9]{5,8}$'", name='chk_audit_id_format'),
        sa.CheckConstraint(
            "entity_type IN ('Requirement', 'Risk', 'Control', 'Verification', 'Evidence', 'Compliance_Finding')",
            name='chk_audit_entity_type'
        ),
        sa.CheckConstraint(
            "action IN ('Create', 'Update', 'Delete', 'State_Change', 'AI_Suggestion_Applied')",
            name='chk_audit_action'
        )
    )
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_timestamp', 'audit_logs', [sa.text('timestamp DESC')])
    op.create_index('idx_audit_user', 'audit_logs', ['user_id'])

    # Append-only trigger for audit logs
    op.execute("""
        CREATE OR REPLACE FUNCTION fn_audit_logs_append_only()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are strictly append-only. Modification and deletion of audit records is strictly prohibited.';
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_audit_logs_append_only
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION fn_audit_logs_append_only();
    """)


def downgrade() -> None:
    # Drop triggers and helper functions
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs;")
    op.execute("DROP FUNCTION IF EXISTS fn_audit_logs_append_only();")
    op.execute("DROP TRIGGER IF EXISTS trg_requirements_last_modified ON requirements;")
    op.execute("DROP FUNCTION IF EXISTS fn_update_last_modified_date();")

    # Drop tables in reverse dependency order
    op.drop_table('audit_logs')
    op.drop_table('compliance_findings')
    op.drop_table('evidence')
    op.drop_table('verifications')
    op.drop_table('controls')
    op.drop_table('risks')
    op.drop_table('requirements')
