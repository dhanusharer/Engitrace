-- =============================================================================
-- EngiTrace AI — Physical PostgreSQL Database Schema
-- Document Reference: DOC-ENG-DDICT-001 (Approved for Implementation)
-- Canonical Flow: Requirement -> Risk -> Control -> Verification -> Evidence -> Compliance
-- Governing Axiom: "AI suggests. Rules validate. Humans approve. The system records."
-- =============================================================================

-- Clean up existing triggers, functions, and tables in reverse dependency order
DROP TRIGGER IF EXISTS trg_audit_logs_append_only ON audit_logs;
DROP TRIGGER IF EXISTS trg_requirements_last_modified ON requirements;
DROP FUNCTION IF EXISTS fn_audit_logs_append_only();
DROP FUNCTION IF EXISTS fn_update_last_modified_date();

DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS compliance_findings CASCADE;
DROP TABLE IF EXISTS evidence CASCADE;
DROP TABLE IF EXISTS verifications CASCADE;
DROP TABLE IF EXISTS controls CASCADE;
DROP TABLE IF EXISTS risks CASCADE;
DROP TABLE IF EXISTS requirements CASCADE;

-- =============================================================================
-- 1. REQUIREMENTS TABLE
-- Foundational systems engineering constraints (ISO/IEC/IEEE 29148, INCOSE)
-- =============================================================================
CREATE TABLE requirements (
    req_id VARCHAR(32) PRIMARY KEY,
    version VARCHAR(16) NOT NULL DEFAULT 'v1.0',
    description TEXT NOT NULL,
    category VARCHAR(32) NOT NULL,
    rationale TEXT NOT NULL,
    source VARCHAR(128) NOT NULL,
    priority VARCHAR(16) NOT NULL,
    owner VARCHAR(64),
    verification_method VARCHAR(32) NOT NULL,
    acceptance_criteria TEXT NOT NULL,
    status VARCHAR(24) NOT NULL DEFAULT 'Draft',
    created_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Epistemic & Data Dictionary Constraints
    CONSTRAINT chk_req_id_format CHECK (req_id ~ '^REQ-[A-Z]{3}-[A-Z]{3}-[0-9]{3,4}$'),
    CONSTRAINT chk_req_category CHECK (category IN (
        'Structural_Loading',
        'Aerodynamic_Performance',
        'Fatigue_Life',
        'Material_Integrity',
        'Geometric_Constraints',
        'Manufacturing_Quality',
        'Environmental_Survivability'
    )),
    CONSTRAINT chk_req_priority CHECK (priority IN (
        'Must_Have',
        'Should_Have',
        'Could_Have',
        'Won_t_Have'
    )),
    CONSTRAINT chk_req_verification_method CHECK (verification_method IN (
        'Analysis',
        'Test',
        'Inspection',
        'Demonstration'
    )),
    CONSTRAINT chk_req_status CHECK (status IN (
        'Draft',
        'Under_Review',
        'Approved',
        'Rejected',
        'Retired'
    )),
    CONSTRAINT chk_req_description_len CHECK (char_length(description) >= 20),
    CONSTRAINT chk_req_rationale_len CHECK (char_length(rationale) >= 15),
    CONSTRAINT chk_req_dates CHECK (last_modified_date >= created_date)
);

CREATE INDEX idx_requirements_category ON requirements(category);
CREATE INDEX idx_requirements_status ON requirements(status);
CREATE INDEX idx_requirements_last_modified ON requirements(last_modified_date);

-- Trigger: Automatically update last_modified_date on modification
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

-- =============================================================================
-- 2. RISKS TABLE
-- Engineering failure modes and hazards threatening requirements (ISO 31000 / FMEA)
-- =============================================================================
CREATE TABLE risks (
    risk_id VARCHAR(32) PRIMARY KEY,
    parent_req_id VARCHAR(32) NOT NULL,
    failure_mode TEXT NOT NULL,
    cause TEXT NOT NULL,
    effect TEXT NOT NULL,
    pre_severity INTEGER NOT NULL,
    pre_likelihood INTEGER NOT NULL,
    detectability INTEGER,
    risk_score INTEGER GENERATED ALWAYS AS (pre_severity * pre_likelihood) STORED,
    risk_category VARCHAR(32) NOT NULL,
    owner VARCHAR(64),
    status VARCHAR(24) NOT NULL DEFAULT 'Identified',

    -- Foreign Key Constraint (Referential integrity strictly preserved)
    CONSTRAINT fk_risks_parent_req FOREIGN KEY (parent_req_id)
        REFERENCES requirements(req_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- Epistemic & Scale Constraints
    CONSTRAINT chk_risk_id_format CHECK (risk_id ~ '^RSK-[A-Z]{3}-[0-9]{3,4}$'),
    CONSTRAINT chk_risk_pre_severity CHECK (pre_severity BETWEEN 1 AND 5),
    CONSTRAINT chk_risk_pre_likelihood CHECK (pre_likelihood BETWEEN 1 AND 5),
    CONSTRAINT chk_risk_detectability CHECK (detectability IS NULL OR detectability BETWEEN 1 AND 5),
    CONSTRAINT chk_risk_category CHECK (risk_category IN (
        'Aerodynamic_Instability',
        'Structural_Yielding',
        'Fatigue_Delamination',
        'Adhesive_Debonding',
        'Buckling_Instability',
        'Environmental_Damage',
        'Manufacturing_Defect'
    )),
    CONSTRAINT chk_risk_status CHECK (status IN (
        'Identified',
        'Under_Assessment',
        'Mitigated',
        'Accepted',
        'Closed'
    ))
);

CREATE INDEX idx_risks_parent_req ON risks(parent_req_id);
CREATE INDEX idx_risks_score ON risks(risk_score);

-- =============================================================================
-- 3. CONTROLS TABLE
-- ISO 12100 3-step risk reduction countermeasures
-- =============================================================================
CREATE TABLE controls (
    control_id VARCHAR(32) PRIMARY KEY,
    parent_risk_id VARCHAR(32) NOT NULL,
    hierarchy_type VARCHAR(32) NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT,
    post_severity INTEGER NOT NULL,
    post_likelihood INTEGER NOT NULL,
    residual_risk INTEGER GENERATED ALWAYS AS (post_severity * post_likelihood) STORED,
    owner VARCHAR(64),
    status VARCHAR(24) NOT NULL DEFAULT 'Proposed',
    implementation_date TIMESTAMPTZ,

    -- Foreign Key Constraint
    CONSTRAINT fk_controls_parent_risk FOREIGN KEY (parent_risk_id)
        REFERENCES risks(risk_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- Epistemic & Scale Constraints
    CONSTRAINT chk_control_id_format CHECK (control_id ~ '^CTRL-[A-Z]{3}-[0-9]{3,4}$'),
    CONSTRAINT chk_control_hierarchy CHECK (hierarchy_type IN (
        'Inherently_Safe_Design',
        'Safeguarding',
        'Information_for_Use'
    )),
    CONSTRAINT chk_control_post_severity CHECK (post_severity BETWEEN 1 AND 5),
    CONSTRAINT chk_control_post_likelihood CHECK (post_likelihood BETWEEN 1 AND 5),
    CONSTRAINT chk_control_status CHECK (status IN (
        'Proposed',
        'Approved',
        'Implemented',
        'Verified',
        'Deprecated'
    )),
    CONSTRAINT chk_control_description_len CHECK (char_length(description) >= 15)
);

CREATE INDEX idx_controls_parent_risk ON controls(parent_risk_id);
CREATE INDEX idx_controls_hierarchy ON controls(hierarchy_type);

-- =============================================================================
-- 4. VERIFICATIONS TABLE
-- Verification plans validating Requirements OR Controls (INCOSE V&V)
-- Dual-target architecture with single-target CHECK constraint
-- =============================================================================
CREATE TABLE verifications (
    verif_id VARCHAR(32) PRIMARY KEY,
    target_type VARCHAR(16) NOT NULL,
    target_req_id VARCHAR(32),
    target_control_id VARCHAR(32),
    method VARCHAR(32) NOT NULL,
    acceptance_crit TEXT NOT NULL,
    reviewer VARCHAR(64),
    status VARCHAR(24) NOT NULL DEFAULT 'Planned',

    -- Foreign Key Constraints (Explicit, physical relational enforcement)
    CONSTRAINT fk_verifications_target_req FOREIGN KEY (target_req_id)
        REFERENCES requirements(req_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,
    CONSTRAINT fk_verifications_target_control FOREIGN KEY (target_control_id)
        REFERENCES controls(control_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- Epistemic & Single-Target Constraints
    CONSTRAINT chk_verif_id_format CHECK (verif_id ~ '^VRF-[A-Z]{3}-[0-9]{3,4}$'),
    CONSTRAINT chk_verif_target_type CHECK (target_type IN ('Requirement', 'Control')),
    CONSTRAINT chk_verif_method CHECK (method IN ('Analysis', 'Test', 'Inspection', 'Demonstration')),
    CONSTRAINT chk_verif_status CHECK (status IN ('Planned', 'In_Progress', 'Passed', 'Failed', 'Blocked')),
    CONSTRAINT chk_verif_acceptance_crit_len CHECK (char_length(acceptance_crit) >= 15),

    -- Strict Single-Target Constraint: Exactly one target key must be populated
    CONSTRAINT chk_verif_single_target CHECK (
        (target_req_id IS NOT NULL AND target_control_id IS NULL) OR
        (target_req_id IS NULL AND target_control_id IS NOT NULL)
    ),

    -- Target Type Consistency Check
    CONSTRAINT chk_verif_target_consistency CHECK (
        (target_type = 'Requirement' AND target_req_id IS NOT NULL) OR
        (target_type = 'Control' AND target_control_id IS NOT NULL)
    )
);

CREATE INDEX idx_verifications_target_req ON verifications(target_req_id);
CREATE INDEX idx_verifications_target_ctrl ON verifications(target_control_id);
CREATE INDEX idx_verifications_status ON verifications(status);

-- =============================================================================
-- 5. EVIDENCE TABLE
-- Immutable physical test logs, reports, and NDE datasets (IEC 61400-23 / DNV)
-- =============================================================================
CREATE TABLE evidence (
    evid_id VARCHAR(32) PRIMARY KEY,
    parent_verif_id VARCHAR(32) NOT NULL,
    evidence_type VARCHAR(32) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    artifact_ref VARCHAR(512) NOT NULL,
    hash VARCHAR(64),
    result_value TEXT,
    date_generated TIMESTAMPTZ NOT NULL,
    approval_status VARCHAR(24) NOT NULL DEFAULT 'Uploaded',

    -- Foreign Key Constraint
    CONSTRAINT fk_evidence_parent_verif FOREIGN KEY (parent_verif_id)
        REFERENCES verifications(verif_id)
        ON UPDATE CASCADE
        ON DELETE RESTRICT,

    -- Epistemic Constraints
    CONSTRAINT chk_evid_id_format CHECK (evid_id ~ '^EVD-[A-Z]{3}-[0-9]{3,4}$'),
    CONSTRAINT chk_evid_type CHECK (evidence_type IN (
        'Simulation_Report',
        'Test_Data_Log',
        'UT_Scan',
        'Material_Certificate',
        'Visual_Inspection_Log',
        'Calibration_Record'
    )),
    CONSTRAINT chk_evid_approval_status CHECK (approval_status IN (
        'Uploaded',
        'Under_Review',
        'Approved',
        'Rejected',
        'Superseded'
    )),
    CONSTRAINT chk_evid_artifact_ref_nonempty CHECK (char_length(trim(artifact_ref)) > 0),
    CONSTRAINT chk_evid_hash_format CHECK (hash IS NULL OR hash ~ '^[a-fA-F0-9]{64}$')
);

CREATE INDEX idx_evidence_parent_verif ON evidence(parent_verif_id);
CREATE INDEX idx_evidence_date ON evidence(date_generated);
CREATE INDEX idx_evidence_type ON evidence(evidence_type);

-- =============================================================================
-- 6. COMPLIANCE FINDINGS TABLE
-- Deterministic engine audit findings targeting any thread node
-- Note: target_entity_id is an application-level logical reference across tables
-- =============================================================================
CREATE TABLE compliance_findings (
    finding_id VARCHAR(32) PRIMARY KEY,
    target_entity_type VARCHAR(32) NOT NULL,
    target_entity_id VARCHAR(32) NOT NULL,
    rule_violated VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    message TEXT NOT NULL,
    finding_status VARCHAR(24) NOT NULL DEFAULT 'Open',
    created_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_date TIMESTAMPTZ,
    resolution TEXT,
    assigned_to VARCHAR(64),

    -- Constraints
    CONSTRAINT chk_finding_id_format CHECK (finding_id ~ '^CMP-[A-Z]{3}-[0-9]{3,4}$'),
    CONSTRAINT chk_finding_target_entity_type CHECK (target_entity_type IN (
        'Requirement',
        'Risk',
        'Control',
        'Verification',
        'Evidence',
        'Subsystem'
    )),
    CONSTRAINT chk_finding_severity CHECK (severity IN ('ERROR', 'WARNING', 'INFO')),
    CONSTRAINT chk_finding_status CHECK (finding_status IN (
        'Open',
        'Under_Investigation',
        'Resolved',
        'Waived'
    )),
    CONSTRAINT chk_finding_dates CHECK (resolved_date IS NULL OR resolved_date >= created_date),
    CONSTRAINT chk_finding_message_len CHECK (char_length(message) >= 15)
);

CREATE INDEX idx_findings_target ON compliance_findings(target_entity_type, target_entity_id);
CREATE INDEX idx_findings_severity ON compliance_findings(severity);
CREATE INDEX idx_findings_status ON compliance_findings(finding_status);

-- =============================================================================
-- 7. AUDIT LOGS TABLE
-- Immutable, chronological provenance ledger (IECRE OD-501)
-- Stores JSONB state diffs; strictly append-only
-- =============================================================================
CREATE TABLE audit_logs (
    log_id VARCHAR(32) PRIMARY KEY,
    entity_type VARCHAR(32) NOT NULL,
    entity_id VARCHAR(32) NOT NULL,
    action VARCHAR(24) NOT NULL,
    field_name VARCHAR(64),
    previous_value JSONB,
    new_value JSONB NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    reason TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CONSTRAINT chk_audit_id_format CHECK (log_id ~ '^LOG-[0-9]{5,8}$'),
    CONSTRAINT chk_audit_entity_type CHECK (entity_type IN (
        'Requirement',
        'Risk',
        'Control',
        'Verification',
        'Evidence',
        'Compliance_Finding'
    )),
    CONSTRAINT chk_audit_action CHECK (action IN (
        'Create',
        'Update',
        'Delete',
        'State_Change',
        'AI_Suggestion_Applied'
    ))
);

CREATE INDEX idx_audit_entity ON audit_logs(entity_type, entity_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp DESC);
CREATE INDEX idx_audit_user ON audit_logs(user_id);

-- Append-Only Enforcement Trigger: Disallow UPDATE and DELETE operations
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
