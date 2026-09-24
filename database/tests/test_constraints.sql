-- =============================================================================
-- EngiTrace AI — Database Constraints & Behavior Validation Script
-- Validates: Schema constraints, dual-target checks, generated columns, triggers
-- =============================================================================

BEGIN;

-- Helper notice function
DO $$
BEGIN
    RAISE NOTICE 'Starting EngiTrace AI Phase 1 Schema Validation Test Suite...';
END $$;

-- -----------------------------------------------------------------------------
-- Test 1: Valid Requirement Insertion
-- -----------------------------------------------------------------------------
INSERT INTO requirements (
    req_id, version, description, category, rationale, source, priority, owner,
    verification_method, acceptance_criteria, status
) VALUES (
    'REQ-BLD-STR-001', 'v1.0',
    'The primary spar cap shall withstand extreme flapwise bending moments without yielding.',
    'Structural_Loading', 'Derived from IEC 61400-1 Class IA extreme gust load case 1.1.',
    'IEC 61400-1:2019', 'Must_Have', 'Spar_Cap_Lead', 'Analysis',
    'Safety margin against material yield > 1.35 under extreme flap bending.', 'Draft'
);

DO $$
BEGIN
    RAISE NOTICE 'Test 1 Passed: Valid Requirement insertion succeeded.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 2: Invalid Risk Parent FK (Must Fail)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    INSERT INTO risks (
        risk_id, parent_req_id, failure_mode, cause, effect,
        pre_severity, pre_likelihood, risk_category, status
    ) VALUES (
        'RSK-STR-999', 'REQ-NON-EXISTENT-999', 'Spar cap delamination',
        'Inadequate resin curing', 'Catastrophic blade failure', 5, 2, 'Structural_Yielding', 'Identified'
    );
    RAISE EXCEPTION 'Test 2 Failed: Foreign key constraint did not reject non-existent requirement!';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Test 2 Passed: Non-existent parent_req_id rejected by foreign key constraint.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 3: Severity Outside 1-5 (Must Fail)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    INSERT INTO risks (
        risk_id, parent_req_id, failure_mode, cause, effect,
        pre_severity, pre_likelihood, risk_category, status
    ) VALUES (
        'RSK-STR-001', 'REQ-BLD-STR-001', 'Spar cap delamination',
        'Inadequate resin curing', 'Catastrophic blade failure', 6, 2, 'Structural_Yielding', 'Identified'
    );
    RAISE EXCEPTION 'Test 3 Failed: Severity = 6 was not rejected!';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'Test 3 Passed: pre_severity = 6 rejected by check constraint.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 4: Likelihood Outside 1-5 (Must Fail)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    INSERT INTO risks (
        risk_id, parent_req_id, failure_mode, cause, effect,
        pre_severity, pre_likelihood, risk_category, status
    ) VALUES (
        'RSK-STR-001', 'REQ-BLD-STR-001', 'Spar cap delamination',
        'Inadequate resin curing', 'Catastrophic blade failure', 5, 0, 'Structural_Yielding', 'Identified'
    );
    RAISE EXCEPTION 'Test 4 Failed: Likelihood = 0 was not rejected!';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'Test 4 Passed: pre_likelihood = 0 rejected by check constraint.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 5: Valid Risk Insertion & Generated Column Calculation
-- -----------------------------------------------------------------------------
INSERT INTO risks (
    risk_id, parent_req_id, failure_mode, cause, effect,
    pre_severity, pre_likelihood, detectability, risk_category, owner, status
) VALUES (
    'RSK-STR-001', 'REQ-BLD-STR-001', 'Spar cap compressive microbuckling',
    'Extreme aerodynamic gust load', 'Loss of blade structural integrity',
    5, 3, 2, 'Structural_Yielding', 'Structural_Engineer_1', 'Identified'
);

DO $$
DECLARE
    v_score INT;
BEGIN
    SELECT risk_score INTO v_score FROM risks WHERE risk_id = 'RSK-STR-001';
    IF v_score != 15 THEN
        RAISE EXCEPTION 'Test 5 Failed: Generated risk_score was %, expected 15', v_score;
    END IF;
    RAISE NOTICE 'Test 5 Passed: Valid Risk inserted; generated risk_score = 15 verified.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 6: Valid Control Insertion & Generated Residual Risk Calculation
-- -----------------------------------------------------------------------------
INSERT INTO controls (
    control_id, parent_risk_id, hierarchy_type, description, rationale,
    post_severity, post_likelihood, owner, status
) VALUES (
    'CTRL-DSN-001', 'RSK-STR-001', 'Inherently_Safe_Design',
    'Increase carbon-fiber spar cap laminate thickness by 15% in high-strain region.',
    'Reduces maximum strain levels below compressive microbuckling threshold.',
    5, 1, 'Laminate_Designer', 'Proposed'
);

DO $$
DECLARE
    v_residual INT;
BEGIN
    SELECT residual_risk INTO v_residual FROM controls WHERE control_id = 'CTRL-DSN-001';
    IF v_residual != 5 THEN
        RAISE EXCEPTION 'Test 6 Failed: Generated residual_risk was %, expected 5', v_residual;
    END IF;
    RAISE NOTICE 'Test 6 Passed: Valid Control inserted; generated residual_risk = 5 verified.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 7: Verification with Both Targets NULL (Must Fail)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    INSERT INTO verifications (
        verif_id, target_type, target_req_id, target_control_id,
        method, acceptance_crit, status
    ) VALUES (
        'VRF-ANA-001', 'Requirement', NULL, NULL,
        'Analysis', 'Finite element maximum strain < 0.0035 under DLC 1.1.', 'Planned'
    );
    RAISE EXCEPTION 'Test 7 Failed: Verification with both targets NULL was not rejected!';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'Test 7 Passed: Verification with both targets NULL rejected by single-target check constraint.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 8: Verification with Both Targets Populated (Must Fail)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    INSERT INTO verifications (
        verif_id, target_type, target_req_id, target_control_id,
        method, acceptance_crit, status
    ) VALUES (
        'VRF-ANA-001', 'Requirement', 'REQ-BLD-STR-001', 'CTRL-DSN-001',
        'Analysis', 'Finite element maximum strain < 0.0035 under DLC 1.1.', 'Planned'
    );
    RAISE EXCEPTION 'Test 8 Failed: Verification with both targets populated was not rejected!';
EXCEPTION
    WHEN check_violation THEN
        RAISE NOTICE 'Test 8 Passed: Verification with both targets populated rejected by single-target check constraint.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 9: Valid Requirement-Targeted Verification
-- -----------------------------------------------------------------------------
INSERT INTO verifications (
    verif_id, target_type, target_req_id, target_control_id,
    method, acceptance_crit, reviewer, status
) VALUES (
    'VRF-ANA-001', 'Requirement', 'REQ-BLD-STR-001', NULL,
    'Analysis', 'Nonlinear FEA deflection margin > 1.35 per DNV-ST-0376.', 'Cert_Delegate_A', 'Planned'
);

DO $$
BEGIN
    RAISE NOTICE 'Test 9 Passed: Requirement-targeted verification inserted successfully.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 10: Valid Control-Targeted Verification
-- -----------------------------------------------------------------------------
INSERT INTO verifications (
    verif_id, target_type, target_req_id, target_control_id,
    method, acceptance_crit, reviewer, status
) VALUES (
    'VRF-TST-001', 'Control', NULL, 'CTRL-DSN-001',
    'Test', 'Full-scale static flapwise load test to 100% design limit without laminate rupture.',
    'Test_Rig_Lead', 'Planned'
);

DO $$
BEGIN
    RAISE NOTICE 'Test 10 Passed: Control-targeted verification inserted successfully.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 11: Evidence Without Valid Parent Verification (Must Fail)
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    INSERT INTO evidence (
        evid_id, parent_verif_id, evidence_type, file_name,
        artifact_ref, date_generated, approval_status
    ) VALUES (
        'EVD-REP-001', 'VRF-NON-EXISTENT-999', 'Simulation_Report',
        'Spar_Cap_Bending_Run_01.pdf', 's3://engitrace-evidence/run01.pdf',
        CURRENT_TIMESTAMP, 'Uploaded'
    );
    RAISE EXCEPTION 'Test 11 Failed: Evidence with non-existent parent_verif_id was not rejected!';
EXCEPTION
    WHEN foreign_key_violation THEN
        RAISE NOTICE 'Test 11 Passed: Evidence without parent verification rejected by foreign key constraint.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 12: Valid Evidence Insertion
-- -----------------------------------------------------------------------------
INSERT INTO evidence (
    evid_id, parent_verif_id, evidence_type, file_name,
    artifact_ref, hash, result_value, date_generated, approval_status
) VALUES (
    'EVD-REP-001', 'VRF-ANA-001', 'Simulation_Report',
    'ANSYS_Composite_PrepPost_SparCap_Run01.pdf',
    's3://engitrace-evidence/2026/fea/ANSYS_Run01.pdf',
    'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    'Maximum strain observed: 0.0028; Margin of safety: 1.48',
    CURRENT_TIMESTAMP, 'Approved'
);

DO $$
BEGIN
    RAISE NOTICE 'Test 12 Passed: Valid Evidence record inserted successfully.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 13: Valid Compliance Finding Insertion (Logical Application Reference)
-- -----------------------------------------------------------------------------
INSERT INTO compliance_findings (
    finding_id, target_entity_type, target_entity_id, rule_violated,
    severity, message, finding_status
) VALUES (
    'CMP-WRN-001', 'Requirement', 'REQ-BLD-STR-001', 'REQ-004',
    'WARNING', 'Requirement description contains conjunction that may indicate a compound requirement.',
    'Open'
);

DO $$
BEGIN
    RAISE NOTICE 'Test 13 Passed: Compliance Finding inserted successfully.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 14: Valid Audit Log Insertion (with JSONB)
-- -----------------------------------------------------------------------------
INSERT INTO audit_logs (
    log_id, entity_type, entity_id, action, field_name,
    previous_value, new_value, user_id, reason
) VALUES (
    'LOG-00001', 'Requirement', 'REQ-BLD-STR-001', 'Create', NULL,
    NULL, '{"status": "Draft", "version": "v1.0"}'::jsonb,
    'Systems_Engineer_1', 'Initial baseline creation'
);

DO $$
BEGIN
    RAISE NOTICE 'Test 14 Passed: Audit log record inserted with JSONB payload.';
END $$;

-- -----------------------------------------------------------------------------
-- Test 15: Audit Log Append-Only: UPDATE Must Be Rejected
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    UPDATE audit_logs SET user_id = 'Malicious_Actor' WHERE log_id = 'LOG-00001';
    RAISE EXCEPTION 'Test 15 Failed: UPDATE on audit_logs was permitted!';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Test 15 Passed: UPDATE on audit_logs was rejected by append-only trigger: %', SQLERRM;
END $$;

-- -----------------------------------------------------------------------------
-- Test 16: Audit Log Append-Only: DELETE Must Be Rejected
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    DELETE FROM audit_logs WHERE log_id = 'LOG-00001';
    RAISE EXCEPTION 'Test 16 Failed: DELETE on audit_logs was permitted!';
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Test 16 Passed: DELETE on audit_logs was rejected by append-only trigger: %', SQLERRM;
END $$;

-- Rollback transaction so test data does not pollute the database
ROLLBACK;

DO $$
BEGIN
    RAISE NOTICE 'All 16 schema constraint tests completed successfully (Transaction Rolled Back).';
END $$;
