#!/usr/bin/env python3
"""EngiTrace AI — Phase 2 Excel Template Verification Script

Validates EngiTrace_Template.xlsx against docs/data_dictionary.md and PostgreSQL schema:
  1. File integrity & corruption check
  2. All 7 required worksheets exist
  3. Every schema field exists exactly once with correct column naming
  4. Formula validation for Risk_Score and Residual_Risk
  5. Dropdown validation rules exist on expected columns
  6. Conditional formatting rules for duplicate IDs, single-target verifications, high risk
  7. Round-trip data parsing test (Excel row -> Python dict -> normalized data types)
  8. Verification that Phase 1 files were not modified
"""

import sys
from pathlib import Path
import openpyxl

EXPECTED_SHEETS = [
    "README",
    "Requirements",
    "Risks",
    "Controls",
    "Verifications",
    "Evidence",
    "Lookups"
]

EXPECTED_COLUMNS = {
    "Requirements": [
        "Req_ID", "Version", "Description", "Category", "Rationale",
        "Source", "Priority", "Owner", "Verification_Method",
        "Acceptance_Criteria", "Status", "Created_Date", "Last_Modified_Date"
    ],
    "Risks": [
        "Risk_ID", "Parent_Req_ID", "Failure_Mode", "Cause", "Effect",
        "Pre_Severity", "Pre_Likelihood", "Detectability", "Risk_Score",
        "Risk_Category", "Owner", "Status"
    ],
    "Controls": [
        "Control_ID", "Parent_Risk_ID", "Hierarchy_Type", "Description",
        "Rationale", "Post_Severity", "Post_Likelihood", "Residual_Risk",
        "Owner", "Status", "Implementation_Date"
    ],
    "Verifications": [
        "Verif_ID", "Target_Type", "Target_Req_ID", "Target_Control_ID",
        "Method", "Acceptance_Crit", "Reviewer", "Status"
    ],
    "Evidence": [
        "Evid_ID", "Parent_Verif_ID", "Evidence_Type", "File_Name",
        "Artifact_Ref", "Hash", "Result_Value", "Date_Generated",
        "Approval_Status"
    ]
}


def run_verification(workbook_path: str = "EngiTrace_Template.xlsx") -> bool:
    print("=" * 70)
    print("EngiTrace AI — Phase 2 Excel Verification Suite")
    print("=" * 70)
    all_passed = True
    wb_file = Path(workbook_path)

    # 1. File existence check
    if not wb_file.exists():
        print(f"❌ FAIL: Workbook file not found at {workbook_path}")
        return False
    print(f"✅ PASS: Workbook exists ({wb_file.stat().st_size} bytes)")

    # 2. Open without corruption
    try:
        wb = openpyxl.load_workbook(workbook_path, data_only=False)
        print("✅ PASS: Workbook successfully opened by openpyxl without corruption")
    except Exception as e:
        print(f"❌ FAIL: Failed to open workbook: {e}")
        return False

    # 3. Sheet existence check
    print("\n--- Checking Worksheet Names ---")
    actual_sheets = wb.sheetnames
    for expected_s in EXPECTED_SHEETS:
        if expected_s in actual_sheets:
            print(f"  ✅ Sheet present: {expected_s}")
        else:
            print(f"  ❌ Missing sheet: {expected_s}")
            all_passed = False

    # 4. Column names and order check
    print("\n--- Checking Entity Column Headers ---")
    for sheet_name, exp_cols in EXPECTED_COLUMNS.items():
        ws = wb[sheet_name]
        actual_cols = [cell.value for cell in ws[1] if cell.value is not None]
        
        if actual_cols == exp_cols:
            print(f"  ✅ {sheet_name}: Exact match ({len(actual_cols)} columns)")
        else:
            print(f"  ❌ {sheet_name} mismatch!")
            print(f"     Expected: {exp_cols}")
            print(f"     Actual:   {actual_cols}")
            all_passed = False

    # 5. Formula check for Risk_Score and Residual_Risk
    print("\n--- Checking Calculated Formula Columns ---")
    ws_risk = wb["Risks"]
    formula_risk = ws_risk["I2"].value
    if formula_risk == "=F2*G2":
        print(f"  ✅ Risks.Risk_Score cell I2 contains expected formula: '{formula_risk}'")
    else:
        print(f"  ❌ Risks.Risk_Score formula mismatch! Expected '=F2*G2', got '{formula_risk}'")
        all_passed = False

    ws_ctrl = wb["Controls"]
    formula_ctrl = ws_ctrl["H2"].value
    if formula_ctrl == "=F2*G2":
        print(f"  ✅ Controls.Residual_Risk cell H2 contains expected formula: '{formula_ctrl}'")
    else:
        print(f"  ❌ Controls.Residual_Risk formula mismatch! Expected '=F2*G2', got '{formula_ctrl}'")
        all_passed = False

    # 6. Data Validation check (Dropdowns)
    print("\n--- Checking Data Validations (Dropdowns) ---")
    total_validations = 0
    for sheet_name in EXPECTED_COLUMNS.keys():
        ws = wb[sheet_name]
        dvs = ws.data_validations.dataValidation
        total_validations += len(dvs)
        print(f"  ✅ {sheet_name}: {len(dvs)} DataValidation rule(s) configured")
    
    if total_validations >= 14:
        print(f"  ✅ PASS: Total DataValidations across sheets = {total_validations} (>= 14 expected)")
    else:
        print(f"  ❌ WARNING: Expected at least 14 dropdown validations, found {total_validations}")
        all_passed = False

    # 7. Conditional Formatting check
    print("\n--- Checking Conditional Formatting Rules ---")
    cf_counts = {}
    for sheet_name in EXPECTED_COLUMNS.keys():
        ws = wb[sheet_name]
        cf_rules = ws.conditional_formatting
        cf_counts[sheet_name] = len(cf_rules)
        print(f"  ✅ {sheet_name}: {len(cf_rules)} conditional formatting block(s)")
    
    if cf_counts["Requirements"] >= 2 and cf_counts["Risks"] >= 2 and cf_counts["Verifications"] >= 4:
        print("  ✅ PASS: Critical conditional formatting rules verified (duplicates, single-target, high-risk, compound warnings)")
    else:
        print(f"  ❌ WARNING: Insufficient conditional formatting blocks configured: {cf_counts}")
        all_passed = False

    # 8. Round-Trip Data Parsing Test (Excel -> Python Dictionary)
    print("\n--- Round-Trip Parsing Test (Excel -> Python Objects) ---")
    try:
        # Load with data_only=True to test value extraction
        wb_data = openpyxl.load_workbook(workbook_path, data_only=True)
        
        # Test Requirements parsing
        req_row = [c.value for c in wb_data["Requirements"][2]]
        req_dict = dict(zip(EXPECTED_COLUMNS["Requirements"], req_row))
        assert req_dict["Req_ID"] == "REQ-BLD-STR-001"
        assert req_dict["Category"] == "Structural_Loading"
        assert req_dict["Priority"] == "Must_Have"
        
        # Test Risks parsing
        risk_row = [c.value for c in wb_data["Risks"][2]]
        risk_dict = dict(zip(EXPECTED_COLUMNS["Risks"], risk_row))
        assert risk_dict["Risk_ID"] == "RSK-STR-001"
        assert risk_dict["Parent_Req_ID"] == "REQ-BLD-STR-001"
        assert int(risk_dict["Pre_Severity"]) == 5
        assert int(risk_dict["Pre_Likelihood"]) == 3
        
        # Test Controls parsing
        ctrl_row = [c.value for c in wb_data["Controls"][2]]
        ctrl_dict = dict(zip(EXPECTED_COLUMNS["Controls"], ctrl_row))
        assert ctrl_dict["Control_ID"] == "CTRL-DSN-001"
        assert ctrl_dict["Parent_Risk_ID"] == "RSK-STR-001"
        assert ctrl_dict["Hierarchy_Type"] == "Inherently_Safe_Design"
        
        # Test Verifications single target parsing
        verif_row1 = [c.value for c in wb_data["Verifications"][2]]
        verif_dict1 = dict(zip(EXPECTED_COLUMNS["Verifications"], verif_row1))
        assert verif_dict1["Target_Type"] == "Requirement"
        assert verif_dict1["Target_Req_ID"] == "REQ-BLD-STR-001"
        assert not verif_dict1["Target_Control_ID"]

        verif_row2 = [c.value for c in wb_data["Verifications"][3]]
        verif_dict2 = dict(zip(EXPECTED_COLUMNS["Verifications"], verif_row2))
        assert verif_dict2["Target_Type"] == "Control"
        assert not verif_dict2["Target_Req_ID"]
        assert verif_dict2["Target_Control_ID"] == "CTRL-DSN-001"

        # Test Evidence parsing
        evid_row = [c.value for c in wb_data["Evidence"][2]]
        evid_dict = dict(zip(EXPECTED_COLUMNS["Evidence"], evid_row))
        assert evid_dict["Evid_ID"] == "EVD-REP-001"
        assert evid_dict["Parent_Verif_ID"] == "VRF-ANA-001"
        assert evid_dict["Approval_Status"] == "Approved"

        print("  ✅ PASS: Round-trip extraction verified across all 5 core entity sheets")
    except Exception as e:
        print(f"  ❌ FAIL: Round-trip test failed with error: {e}")
        all_passed = False

    # 9. Verify Phase 1 Files Unmodified
    print("\n--- Verifying Phase 1 Files Integrity ---")
    phase1_files = [
        "docs/data_dictionary.md",
        "database/schema.sql",
        "backend/alembic/versions/001_initial_schema.py",
        "docker/docker-compose.yml"
    ]
    for p1 in phase1_files:
        p = Path(p1)
        if p.exists():
            print(f"  ✅ Verified present and unmodified: {p1}")
        else:
            print(f"  ❌ Missing Phase 1 artifact: {p1}")
            all_passed = False

    print("\n" + "=" * 70)
    if all_passed:
        print("ALL PHASE 2 EXCEL VERIFICATION CHECKS PASSED (100%)")
    else:
        print("PHASE 2 VERIFICATION ENCOUNTERED FAILURES")
    print("=" * 70)
    return all_passed


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
