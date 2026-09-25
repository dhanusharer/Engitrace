#!/usr/bin/env python3
"""EngiTrace AI — Excel Engineering Input Layer Generator

Generates EngiTrace_Template.xlsx adhering strictly to docs/data_dictionary.md.
Includes:
  - Worksheets: Requirements, Risks, Controls, Verifications, Evidence, Lookups, README
  - Standardized column headers matching PostgreSQL schema exactly
  - Data validation dropdowns referencing centralized Lookups sheet
  - Formula-driven calculated columns (Risk_Score, Residual_Risk)
  - Comprehensive conditional formatting (duplicate IDs, single-target verifications, high-risk triage, INCOSE compound-sentence warnings)
  - Freeze panes, auto-filters, and clean engineering styling
  - Small illustrative baseline sample records
"""

import os
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.formatting.rule import CellIsRule, FormulaRule


def create_engitrace_template(output_path: str = "EngiTrace_Template.xlsx") -> None:
    wb = openpyxl.Workbook()
    # Remove default sheet
    default_sheet = wb.active
    wb.remove(default_sheet)

    # -------------------------------------------------------------------------
    # Color Palette & Styling Definitions
    # -------------------------------------------------------------------------
    font_name = "Segoe UI"
    
    font_header_req = Font(name=font_name, size=10, bold=True, color="FFFFFF")
    font_header_opt = Font(name=font_name, size=10, bold=True, color="FFFFFF")
    font_data = Font(name=font_name, size=9.5, bold=False, color="1E293B")
    font_calc = Font(name=font_name, size=9.5, bold=True, color="0F172A")
    font_readme_title = Font(name=font_name, size=16, bold=True, color="0F172A")
    font_readme_h1 = Font(name=font_name, size=12, bold=True, color="1E3A8A")
    font_readme_body = Font(name=font_name, size=10, bold=False, color="334155")
    font_readme_axiom = Font(name=font_name, size=11, bold=True, italic=True, color="1E3A8A")

    fill_header_req = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")  # Deep Navy for Required
    fill_header_opt = PatternFill(start_color="475569", end_color="475569", fill_type="solid")  # Slate Gray for Optional
    fill_header_calc = PatternFill(start_color="065F46", end_color="065F46", fill_type="solid") # Deep Emerald for Calculated
    fill_calc_data = PatternFill(start_color="F0FDF4", end_color="F0FDF4", fill_type="solid")   # Mint tint for calculated cells
    fill_zebra = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")       # Very subtle slate zebra

    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(
        left=thin_border_side, right=thin_border_side,
        top=thin_border_side, bottom=thin_border_side
    )
    header_border = Border(
        left=Side(border_style="thin", color="0F172A"),
        right=Side(border_style="thin", color="0F172A"),
        top=Side(border_style="medium", color="0F172A"),
        bottom=Side(border_style="medium", color="0F172A")
    )

    align_center = Alignment(horizontal="center", vertical="center", wrap_text=True)
    align_left = Alignment(horizontal="left", vertical="center", wrap_text=True)
    align_right = Alignment(horizontal="right", vertical="center", wrap_text=True)
    align_header = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # -------------------------------------------------------------------------
    # 1. README SHEET
    # -------------------------------------------------------------------------
    ws_readme = wb.create_sheet(title="README")
    ws_readme.views.sheetView[0].showGridLines = True

    readme_content = [
        ("EngiTrace AI — Engineering Risk, Compliance & Traceability Platform", font_readme_title),
        ("Digital Thread Template & Engineering Input Layer (Phase 2)", font_readme_h1),
        ("", font_readme_body),
        ("Core Architectural Axiom:", font_readme_h1),
        ('"AI suggests. Rules validate. Humans approve. The system records."', font_readme_axiom),
        ("", font_readme_body),
        ("1. Purpose & Scope", font_readme_h1),
        ("This workbook serves as the standardized engineering data input, review, and import layer for EngiTrace AI. "
         "It models the complete digital engineering thread for wind-turbine blade structural design according to "
         "international systems-engineering principles (ISO/IEC/IEEE 29148, ISO 31000, ISO 12100, IEC 61400-5/23).", font_readme_body),
        ("", font_readme_body),
        ("2. Authoritative Source of Truth", font_readme_h1),
        ("• PostgreSQL is the authoritative system of record. Excel is an engineering authoring and staging interface.", font_readme_body),
        ("• This platform is an educational engineering portfolio prototype. It does NOT perform real finite element analysis (FEA), "
         "computational fluid dynamics (CFD), structural aeroelastic simulation, or autonomous safety certification.", font_readme_body),
        ("• Risk prioritization thresholds (such as Risk_Score >= 15 requiring a mandatory Control) are project-specific triage "
         "conventions [Prototype design decision] and not official regulatory certification limits.", font_readme_body),
        ("", font_readme_body),
        ("3. Canonical Digital Thread Workflow", font_readme_h1),
        ("   Requirement ──> Risk ──> Control ──> Verification ──> Evidence ──> Compliance Finding", font_readme_axiom),
        ("   (Forward: completeness / Backward: root-cause & change impact analysis)", font_readme_body),
        ("", font_readme_body),
        ("4. Instructions for Engineers", font_readme_h1),
        ("Step 1: Enter baseline engineering constraints in the 'Requirements' sheet. Ensure each has rationale and verification method.", font_readme_body),
        ("Step 2: Identify potential physical failure modes in 'Risks' and reference parent Req_ID. Rate Pre_Severity and Pre_Likelihood.", font_readme_body),
        ("Step 3: In 'Controls', implement ISO 12100 countermeasures. Residual_Risk will calculate automatically and must be < parent Risk_Score.", font_readme_body),
        ("Step 4: In 'Verifications', define test/simulation protocols. Exactly ONE target (Requirement OR Control) must be populated.", font_readme_body),
        ("Step 5: Attach verified test/inspection reports in 'Evidence', referencing the originating Verif_ID.", font_readme_body),
        ("Step 6: Review highlighted conditional formatting warnings (red for errors, amber for quality alerts) before exporting to backend.", font_readme_body),
        ("", font_readme_body),
        ("5. Sheet Legend & Header Formatting", font_readme_h1),
        ("• Deep Navy Headers: Mandatory fields required for referential integrity and schema compliance.", font_readme_body),
        ("• Slate Gray Headers: Optional engineering fields (such as secondary rationales, owners, or implementation dates).", font_readme_body),
        ("• Emerald Green Headers: Automatically calculated formula fields (Risk_Score, Residual_Risk). Do NOT edit manually.", font_readme_body),
        ("• Lookups Sheet: Centralized lookup tables driving dropdown validations. Keep protected.", font_readme_body),
    ]

    for row_idx, (text, font) in enumerate(readme_content, start=1):
        cell = ws_readme.cell(row=row_idx, column=2, value=text)
        cell.font = font
        ws_readme.row_dimensions[row_idx].height = 20 if text else 10
    
    ws_readme.column_dimensions["A"].width = 4
    ws_readme.column_dimensions["B"].width = 115

    # -------------------------------------------------------------------------
    # 2. LOOKUPS SHEET
    # -------------------------------------------------------------------------
    ws_lookups = wb.create_sheet(title="Lookups")
    ws_lookups.views.sheetView[0].showGridLines = True

    lookups_data = {
        "RequirementCategory": [
            "Structural_Loading", "Aerodynamic_Performance", "Fatigue_Life",
            "Material_Integrity", "Geometric_Constraints", "Manufacturing_Quality",
            "Environmental_Survivability"
        ],
        "RequirementPriority": ["Must_Have", "Should_Have", "Could_Have", "Won_t_Have"],
        "RequirementStatus": ["Draft", "Under_Review", "Approved", "Rejected", "Retired"],
        "VerificationMethod": ["Analysis", "Test", "Inspection", "Demonstration"],
        "RiskCategory": [
            "Aerodynamic_Instability", "Structural_Yielding", "Fatigue_Delamination",
            "Adhesive_Debonding", "Buckling_Instability", "Environmental_Damage",
            "Manufacturing_Defect"
        ],
        "RiskStatus": ["Identified", "Under_Assessment", "Mitigated", "Accepted", "Closed"],
        "ControlHierarchyType": ["Inherently_Safe_Design", "Safeguarding", "Information_for_Use"],
        "ControlStatus": ["Proposed", "Approved", "Implemented", "Verified", "Deprecated"],
        "VerificationTargetType": ["Requirement", "Control"],
        "VerificationStatus": ["Planned", "In_Progress", "Passed", "Failed", "Blocked"],
        "EvidenceType": [
            "Simulation_Report", "Test_Data_Log", "UT_Scan",
            "Material_Certificate", "Visual_Inspection_Log", "Calibration_Record"
        ],
        "EvidenceApprovalStatus": ["Uploaded", "Under_Review", "Approved", "Rejected", "Superseded"],
        "RatingScale": ["1", "2", "3", "4", "5"]
    }

    lookup_columns = list(lookups_data.keys())
    for col_idx, col_name in enumerate(lookup_columns, start=1):
        c = ws_lookups.cell(row=1, column=col_idx, value=col_name)
        c.font = font_header_req
        c.fill = fill_header_req
        c.alignment = align_center
        c.border = header_border
        
        values = lookups_data[col_name]
        for row_idx, val in enumerate(values, start=2):
            cell = ws_lookups.cell(row=row_idx, column=col_idx, value=val)
            cell.font = font_data
            cell.alignment = align_left
            cell.border = cell_border
        
        col_letter = get_column_letter(col_idx)
        max_len = max(len(col_name), max(len(str(v)) for v in values))
        ws_lookups.column_dimensions[col_letter].width = max(max_len + 4, 15)

    ws_lookups.row_dimensions[1].height = 24

    # -------------------------------------------------------------------------
    # Helper: Entity Sheet Configuration Builder
    # -------------------------------------------------------------------------
    def setup_entity_sheet(sheet_title, columns_def, sample_rows):
        ws = wb.create_sheet(title=sheet_title)
        ws.views.sheetView[0].showGridLines = True
        ws.freeze_panes = "A2"
        ws.row_dimensions[1].height = 26

        # Write Header Row
        for col_idx, col_info in enumerate(columns_def, start=1):
            col_name = col_info["name"]
            is_req = col_info.get("required", False)
            is_calc = col_info.get("calculated", False)

            cell = ws.cell(row=1, column=col_idx, value=col_name)
            cell.alignment = align_header
            cell.border = header_border
            
            if is_calc:
                cell.font = font_header_req
                cell.fill = fill_header_calc
            elif is_req:
                cell.font = font_header_req
                cell.fill = fill_header_req
            else:
                cell.font = font_header_opt
                cell.fill = fill_header_opt

        # Write Sample Rows
        for row_offset, row_data in enumerate(sample_rows, start=2):
            ws.row_dimensions[row_offset].height = 22
            for col_idx, col_info in enumerate(columns_def, start=1):
                col_name = col_info["name"]
                is_calc = col_info.get("calculated", False)
                val = row_data.get(col_name, "")
                
                cell = ws.cell(row=row_offset, column=col_idx)
                if is_calc and col_info.get("formula"):
                    cell.value = col_info["formula"](row_offset)
                    cell.font = font_calc
                    cell.fill = fill_calc_data
                else:
                    cell.value = val
                    cell.font = font_data
                    if row_offset % 2 == 1:
                        cell.fill = fill_zebra
                
                cell.border = cell_border
                
                # Alignment logic
                if col_info.get("align") == "center":
                    cell.alignment = align_center
                elif col_info.get("align") == "right":
                    cell.alignment = align_right
                else:
                    cell.alignment = align_left

        # Calculate Column Widths
        for col_idx, col_info in enumerate(columns_def, start=1):
            col_letter = get_column_letter(col_idx)
            suggested_width = col_info.get("width", 18)
            ws.column_dimensions[col_letter].width = suggested_width

        # Set AutoFilter
        last_col = get_column_letter(len(columns_def))
        last_row = max(len(sample_rows) + 1, 2)
        ws.auto_filter.ref = f"A1:{last_col}{last_row}"

        return ws

    # -------------------------------------------------------------------------
    # 3. REQUIREMENTS SHEET
    # -------------------------------------------------------------------------
    req_columns = [
        {"name": "Req_ID", "required": True, "align": "center", "width": 20},
        {"name": "Version", "required": True, "align": "center", "width": 12},
        {"name": "Description", "required": True, "align": "left", "width": 46},
        {"name": "Category", "required": True, "align": "center", "width": 26, "lookup_range": "Lookups!$A$2:$A$8"},
        {"name": "Rationale", "required": True, "align": "left", "width": 40},
        {"name": "Source", "required": True, "align": "left", "width": 24},
        {"name": "Priority", "required": True, "align": "center", "width": 16, "lookup_range": "Lookups!$B$2:$B$5"},
        {"name": "Owner", "required": False, "align": "center", "width": 22},
        {"name": "Verification_Method", "required": True, "align": "center", "width": 22, "lookup_range": "Lookups!$D$2:$D$5"},
        {"name": "Acceptance_Criteria", "required": True, "align": "left", "width": 38},
        {"name": "Status", "required": True, "align": "center", "width": 16, "lookup_range": "Lookups!$C$2:$C$6"},
        {"name": "Created_Date", "required": True, "align": "center", "width": 22},
        {"name": "Last_Modified_Date", "required": True, "align": "center", "width": 22},
    ]

    req_samples = [
        {
            "Req_ID": "REQ-BLD-STR-001",
            "Version": "v1.0",
            "Description": "The primary spar cap shall withstand extreme flapwise bending moments without composite laminate yield.",
            "Category": "Structural_Loading",
            "Rationale": "Derived from IEC 61400-1 Class IA extreme gust load case 1.1.",
            "Source": "IEC 61400-1:2019 Sec 7.4",
            "Priority": "Must_Have",
            "Owner": "Spar_Cap_Structural_Lead",
            "Verification_Method": "Analysis",
            "Acceptance_Criteria": "Flapwise bending strain margin > 1.35 under 15,000 kNm ultimate load.",
            "Status": "Approved",
            "Created_Date": "2026-01-15T08:30:00Z",
            "Last_Modified_Date": "2026-01-15T08:30:00Z"
        },
        {
            "Req_ID": "REQ-BLD-FAT-002",
            "Version": "v1.0",
            "Description": "The trailing edge adhesive bondline shall sustain 25-year cyclic fatigue loading without progressive debonding.",
            "Category": "Fatigue_Life",
            "Rationale": "Edgewise gravity and turbulent shear cycling dictates trailing edge structural integrity.",
            "Source": "DNV-ST-0376 Sec 5.3",
            "Priority": "Must_Have",
            "Owner": "Blade_Materials_Group",
            "Verification_Method": "Analysis",
            "Acceptance_Criteria": "Damage Equivalent Load (DEL) margin > 1.40 under 10^7 load cycles.",
            "Status": "Approved",
            "Created_Date": "2026-01-18T10:00:00Z",
            "Last_Modified_Date": "2026-01-18T10:00:00Z"
        }
    ]

    ws_req = setup_entity_sheet("Requirements", req_columns, req_samples)

    # -------------------------------------------------------------------------
    # 4. RISKS SHEET
    # -------------------------------------------------------------------------
    risk_columns = [
        {"name": "Risk_ID", "required": True, "align": "center", "width": 18},
        {"name": "Parent_Req_ID", "required": True, "align": "center", "width": 20},
        {"name": "Failure_Mode", "required": True, "align": "left", "width": 36},
        {"name": "Cause", "required": True, "align": "left", "width": 36},
        {"name": "Effect", "required": True, "align": "left", "width": 36},
        {"name": "Pre_Severity", "required": True, "align": "center", "width": 14, "lookup_range": "Lookups!$M$2:$M$6"},
        {"name": "Pre_Likelihood", "required": True, "align": "center", "width": 14, "lookup_range": "Lookups!$M$2:$M$6"},
        {"name": "Detectability", "required": False, "align": "center", "width": 14, "lookup_range": "Lookups!$M$2:$M$6"},
        {"name": "Risk_Score", "required": True, "calculated": True, "align": "center", "width": 14, "formula": lambda r: f"=F{r}*G{r}"},
        {"name": "Risk_Category", "required": True, "align": "center", "width": 26, "lookup_range": "Lookups!$E$2:$E$8"},
        {"name": "Owner", "required": False, "align": "center", "width": 22},
        {"name": "Status", "required": True, "align": "center", "width": 18, "lookup_range": "Lookups!$F$2:$F$6"},
    ]

    risk_samples = [
        {
            "Risk_ID": "RSK-STR-001",
            "Parent_Req_ID": "REQ-BLD-STR-001",
            "Failure_Mode": "Carbon spar cap compressive microbuckling",
            "Cause": "Extreme 50-year aerodynamic gust loading exceeding compressive laminate threshold",
            "Effect": "Loss of structural flapwise bending resistance, potential catastrophic blade separation",
            "Pre_Severity": 5,
            "Pre_Likelihood": 3,
            "Detectability": 2,
            "Risk_Category": "Structural_Yielding",
            "Owner": "Lead_Structural_Engineer",
            "Status": "Mitigated"
        },
        {
            "Risk_ID": "RSK-FAT-002",
            "Parent_Req_ID": "REQ-BLD-FAT-002",
            "Failure_Mode": "Trailing edge adhesive peeling crack propagation",
            "Cause": "Resin void content and cyclic edgewise shear fatigue stress",
            "Effect": "Aeroelastic fluttering and loss of trailing edge aerodynamic contour",
            "Pre_Severity": 4,
            "Pre_Likelihood": 3,
            "Detectability": 3,
            "Risk_Category": "Adhesive_Debonding",
            "Owner": "Adhesives_Specialist",
            "Status": "Mitigated"
        }
    ]

    ws_risk = setup_entity_sheet("Risks", risk_columns, risk_samples)

    # -------------------------------------------------------------------------
    # 5. CONTROLS SHEET
    # -------------------------------------------------------------------------
    ctrl_columns = [
        {"name": "Control_ID", "required": True, "align": "center", "width": 18},
        {"name": "Parent_Risk_ID", "required": True, "align": "center", "width": 18},
        {"name": "Hierarchy_Type", "required": True, "align": "center", "width": 26, "lookup_range": "Lookups!$G$2:$G$4"},
        {"name": "Description", "required": True, "align": "left", "width": 42},
        {"name": "Rationale", "required": False, "align": "left", "width": 36},
        {"name": "Post_Severity", "required": True, "align": "center", "width": 14, "lookup_range": "Lookups!$M$2:$M$6"},
        {"name": "Post_Likelihood", "required": True, "align": "center", "width": 14, "lookup_range": "Lookups!$M$2:$M$6"},
        {"name": "Residual_Risk", "required": True, "calculated": True, "align": "center", "width": 15, "formula": lambda r: f"=F{r}*G{r}"},
        {"name": "Owner", "required": False, "align": "center", "width": 22},
        {"name": "Status", "required": True, "align": "center", "width": 16, "lookup_range": "Lookups!$H$2:$H$6"},
        {"name": "Implementation_Date", "required": False, "align": "center", "width": 22},
    ]

    ctrl_samples = [
        {
            "Control_ID": "CTRL-DSN-001",
            "Parent_Risk_ID": "RSK-STR-001",
            "Hierarchy_Type": "Inherently_Safe_Design",
            "Description": "Increase carbon-fiber spar cap laminate stack thickness by 15% in high-strain region (0.35R to 0.65R).",
            "Rationale": "Reduces peak compressive strain below microbuckling limit under extreme flap bending.",
            "Post_Severity": 5,
            "Post_Likelihood": 1,
            "Owner": "Laminate_Design_Team",
            "Status": "Implemented",
            "Implementation_Date": "2026-03-20T14:00:00Z"
        },
        {
            "Control_ID": "CTRL-MAT-002",
            "Parent_Risk_ID": "RSK-FAT-002",
            "Hierarchy_Type": "Inherently_Safe_Design",
            "Description": "Formulate high-toughness polyurethane structural adhesive with enhanced cyclic fracture toughness.",
            "Rationale": "Suppresses micro-crack initiation along trailing edge bondline interface under peel cycling.",
            "Post_Severity": 3,
            "Post_Likelihood": 2,
            "Owner": "Materials_Infusion_Group",
            "Status": "Implemented",
            "Implementation_Date": "2026-04-10T09:30:00Z"
        }
    ]

    ws_ctrl = setup_entity_sheet("Controls", ctrl_columns, ctrl_samples)

    # -------------------------------------------------------------------------
    # 6. VERIFICATIONS SHEET
    # -------------------------------------------------------------------------
    verif_columns = [
        {"name": "Verif_ID", "required": True, "align": "center", "width": 18},
        {"name": "Target_Type", "required": True, "align": "center", "width": 16, "lookup_range": "Lookups!$I$2:$I$3"},
        {"name": "Target_Req_ID", "required": False, "align": "center", "width": 20},
        {"name": "Target_Control_ID", "required": False, "align": "center", "width": 20},
        {"name": "Method", "required": True, "align": "center", "width": 18, "lookup_range": "Lookups!$D$2:$D$5"},
        {"name": "Acceptance_Crit", "required": True, "align": "left", "width": 42},
        {"name": "Reviewer", "required": False, "align": "center", "width": 22},
        {"name": "Status", "required": True, "align": "center", "width": 16, "lookup_range": "Lookups!$J$2:$J$6"},
    ]

    verif_samples = [
        {
            "Verif_ID": "VRF-ANA-001",
            "Target_Type": "Requirement",
            "Target_Req_ID": "REQ-BLD-STR-001",
            "Target_Control_ID": "",
            "Method": "Analysis",
            "Acceptance_Crit": "Nonlinear FEA maximum strain < 0.0035 under extreme DLC 1.1 gust loading.",
            "Reviewer": "Chief_Certification_Engineer",
            "Status": "Passed"
        },
        {
            "Verif_ID": "VRF-TST-002",
            "Target_Type": "Control",
            "Target_Req_ID": "",
            "Target_Control_ID": "CTRL-DSN-001",
            "Method": "Test",
            "Acceptance_Crit": "Full-scale static flapwise bending load test to 100% design limit without acoustic emissions burst.",
            "Reviewer": "Test_Rig_Lead",
            "Status": "Passed"
        }
    ]

    ws_verif = setup_entity_sheet("Verifications", verif_columns, verif_samples)

    # -------------------------------------------------------------------------
    # 7. EVIDENCE SHEET
    # -------------------------------------------------------------------------
    evid_columns = [
        {"name": "Evid_ID", "required": True, "align": "center", "width": 18},
        {"name": "Parent_Verif_ID", "required": True, "align": "center", "width": 18},
        {"name": "Evidence_Type", "required": True, "align": "center", "width": 24, "lookup_range": "Lookups!$K$2:$K$7"},
        {"name": "File_Name", "required": True, "align": "left", "width": 36},
        {"name": "Artifact_Ref", "required": True, "align": "left", "width": 46},
        {"name": "Hash", "required": False, "align": "center", "width": 32},
        {"name": "Result_Value", "required": False, "align": "left", "width": 36},
        {"name": "Date_Generated", "required": True, "align": "center", "width": 22},
        {"name": "Approval_Status", "required": True, "align": "center", "width": 18, "lookup_range": "Lookups!$L$2:$L$6"},
    ]

    evid_samples = [
        {
            "Evid_ID": "EVD-REP-001",
            "Parent_Verif_ID": "VRF-ANA-001",
            "Evidence_Type": "Simulation_Report",
            "File_Name": "ANSYS_Flapwise_Bending_Run04_Report.pdf",
            "Artifact_Ref": "s3://engitrace-blade-evidence/2026/fea/ANSYS_Run04.pdf",
            "Hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "Result_Value": "Maximum strain observed: 0.0029; Safety margin: 1.42 against allowable limit.",
            "Date_Generated": "2026-05-10T11:45:00Z",
            "Approval_Status": "Approved"
        },
        {
            "Evid_ID": "EVD-LOG-002",
            "Parent_Verif_ID": "VRF-TST-002",
            "Evidence_Type": "Test_Data_Log",
            "File_Name": "FullScale_Static_Flapwise_Load_Run02.csv",
            "Artifact_Ref": "s3://engitrace-blade-evidence/2026/tests/Rig01_Run02.csv",
            "Hash": "ca978112ca1bbdcafac231b39a23dc4da786081496140970e4769c72c4c970f2",
            "Result_Value": "Peak load sustained: 15,250 kNm; zero permanent plastic deformation observed.",
            "Date_Generated": "2026-06-18T16:20:00Z",
            "Approval_Status": "Approved"
        }
    ]

    ws_evid = setup_entity_sheet("Evidence", evid_columns, evid_samples)

    # -------------------------------------------------------------------------
    # 8. Attach Data Validations (Dropdown Lists)
    # -------------------------------------------------------------------------
    sheet_col_map = {
        "Requirements": (ws_req, req_columns),
        "Risks": (ws_risk, risk_columns),
        "Controls": (ws_ctrl, ctrl_columns),
        "Verifications": (ws_verif, verif_columns),
        "Evidence": (ws_evid, evid_columns),
    }

    max_rows = 500  # Apply validation for up to 500 rows of user entry

    for sheet_name, (ws, cols) in sheet_col_map.items():
        for col_idx, col_info in enumerate(cols, start=1):
            if "lookup_range" in col_info:
                lookup_ref = col_info["lookup_range"]
                dv = DataValidation(
                    type="list",
                    formula1=f"={lookup_ref}",
                    allow_blank=not col_info.get("required", False),
                    showErrorMessage=True,
                    errorTitle="Invalid Selection",
                    error="Value must be selected from the approved lookup list."
                )
                col_letter = get_column_letter(col_idx)
                dv.add(f"{col_letter}2:{col_letter}{max_rows}")
                ws.add_data_validation(dv)

    # -------------------------------------------------------------------------
    # 9. Conditional Formatting Rules
    # -------------------------------------------------------------------------
    fill_error_red = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
    font_error_red = Font(name=font_name, size=9.5, color="991B1B", bold=True)
    
    fill_warn_amber = PatternFill(start_color="FEF3C7", end_color="FEF3C7", fill_type="solid")
    font_warn_amber = Font(name=font_name, size=9.5, color="92400E", bold=True)

    # Rule A: Duplicate Primary Key Detection across all entity sheets
    for ws in [ws_req, ws_risk, ws_ctrl, ws_verif, ws_evid]:
        rule_dup = FormulaRule(
            formula=['COUNTIF($A:$A, $A2)>1'],
            stopIfTrue=True,
            fill=fill_error_red,
            font=font_error_red
        )
        ws.conditional_formatting.add(f"A2:A{max_rows}", rule_dup)

    # Rule B: Requirements: Compound Sentence Warning (contains " and ") per INCOSE R18
    # Rule REQ-004: Quality review warning, NOT hard rejection
    rule_compound = FormulaRule(
        formula=['ISNUMBER(SEARCH(" and ", $C2))'],
        stopIfTrue=False,
        fill=fill_warn_amber,
        font=font_warn_amber
    )
    ws_req.conditional_formatting.add(f"C2:C{max_rows}", rule_compound)

    # Rule C: Risks: High Risk Score Triage Alert (Risk_Score >= 15)
    # Prototype triage convention [Prototype design decision]
    rule_high_risk = CellIsRule(
        operator="greaterThanOrEqual",
        formula=["15"],
        stopIfTrue=True,
        fill=fill_error_red,
        font=font_error_red
    )
    ws_risk.conditional_formatting.add(f"I2:I{max_rows}", rule_high_risk)

    # Rule D: Verifications: Strict Single-Target Rule
    # Exactly ONE of Target_Req_ID or Target_Control_ID must be populated
    # 1. Both populated violation:
    rule_both_pop = FormulaRule(
        formula=['AND($A2<>"", NOT(ISBLANK($C2)), NOT(ISBLANK($D2)))'],
        stopIfTrue=True,
        fill=fill_error_red,
        font=font_error_red
    )
    # 2. Both empty violation:
    rule_both_empty = FormulaRule(
        formula=['AND($A2<>"", ISBLANK($C2), ISBLANK($D2))'],
        stopIfTrue=True,
        fill=fill_error_red,
        font=font_error_red
    )
    # 3. Target Type mismatch:
    rule_mismatch_req = FormulaRule(
        formula=['AND($A2<>"", $B2="Requirement", ISBLANK($C2))'],
        stopIfTrue=True,
        fill=fill_warn_amber,
        font=font_warn_amber
    )
    rule_mismatch_ctrl = FormulaRule(
        formula=['AND($A2<>"", $B2="Control", ISBLANK($D2))'],
        stopIfTrue=True,
        fill=fill_warn_amber,
        font=font_warn_amber
    )

    ws_verif.conditional_formatting.add(f"C2:D{max_rows}", rule_both_pop)
    ws_verif.conditional_formatting.add(f"C2:D{max_rows}", rule_both_empty)
    ws_verif.conditional_formatting.add(f"C2:C{max_rows}", rule_mismatch_req)
    ws_verif.conditional_formatting.add(f"D2:D{max_rows}", rule_mismatch_ctrl)

    # -------------------------------------------------------------------------
    # 10. Sheet Visibility and Ordering
    # -------------------------------------------------------------------------
    # Sheet order: README, Requirements, Risks, Controls, Verifications, Evidence, Lookups
    desired_order = ["README", "Requirements", "Risks", "Controls", "Verifications", "Evidence", "Lookups"]
    wb._sheets = [wb[s] for s in desired_order]
    
    # Hide Lookups sheet so engineers interact only with primary entity sheets
    ws_lookups.sheet_state = "hidden"
    
    # Set README as active tab when opened
    wb.active = ws_readme

    # -------------------------------------------------------------------------
    # 11. Save Workbook
    # -------------------------------------------------------------------------
    output_file = Path(output_path).resolve()
    wb.save(output_file)
    print(f"Successfully generated EngiTrace Excel template: {output_file}")


if __name__ == "__main__":
    create_engitrace_template()
