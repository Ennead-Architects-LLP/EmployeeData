#!/usr/bin/env python3
"""
Standalone GPU Master List Extractor
====================================

Extracts data from EA_US_Desktop_Hardware_GPU_Master List_2025.xlsx
and generates JSON keyed by human full names (First Last).

Usage:
    python extract_gpu_data.py [input_excel] [output_json]

If no arguments provided, uses default paths:
    Input:  EA_US_Desktop_Hardware_GPU_Master List_2025.xlsx
    Output: gpu_data_by_name.json
"""

import json
import os
import re
import sys
from datetime import datetime
from typing import Dict, Any

import pandas as pd


def normalize_name(first: str, last: str) -> str:
    """Normalize first and last name to 'First Last' format."""
    if pd.isna(first) or pd.isna(last):
        return ""
    
    first = str(first).strip()
    last = str(last).strip()
    
    if not first or not last:
        return ""
    
    # Clean and title case
    first = re.sub(r'\s+', ' ', first).title()
    last = re.sub(r'\s+', ' ', last).title()
    
    return f"{first} {last}"


def clean_value(value: Any) -> Any:
    """Clean pandas values for JSON serialization."""
    if pd.isna(value):
        return None
    
    # Handle datetime objects
    if hasattr(value, 'isoformat'):
        try:
            return value.isoformat()
        except:
            return str(value)
    
    # Handle numpy types
    if hasattr(value, 'item'):
        return value.item()
    
    return value


def extract_gpu_data(excel_path: str, output_path: str) -> None:
    """Extract GPU data and save as JSON keyed by full names, grouping multiple computers per person.

    Output structure:
    {
      "First Last": {
        "COMPUTERNAME1": { ... row data ... },
        "COMPUTERNAME2": { ... row data ... }
      }
    }
    """
    
    print(f"Reading Excel file: {excel_path}")
    df = pd.read_excel(excel_path)
    
    # Drop entirely empty columns and auto-generated unnamed columns
    df = df.dropna(axis=1, how='all')
    df = df.loc[:, ~df.columns.astype(str).str.match(r'^Unnamed(?::\\s*\\d+)?$', case=False)]
    print(f"Found {len(df)} records")
    
    # Check required columns
    required_cols = ['First Name', 'Last Name']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Extract data
    result: Dict[str, Dict[str, Any]] = {}
    skipped = 0
    total_rows = 0
    total_computers = 0
    
    for idx, row in df.iterrows():
        total_rows += 1
        # Create full name key
        full_name = normalize_name(row['First Name'], row['Last Name'])
        
        if not full_name:
            skipped += 1
            continue
        
        # Determine computer key
        computername_raw = row.get('Computername') if 'Computername' in df.columns else None
        computer_key = str(computername_raw).strip() if pd.notna(computername_raw) and str(computername_raw).strip() else f"Computer_{idx+1}"
        
        # Clean all row data
        record: Dict[str, Any] = {}
        for col in df.columns:
            record[col] = clean_value(row[col])
        
        # Add to result under person's dict (direct computer dict)
        person_entry = result.setdefault(full_name, {})
        person_entry[computer_key] = record
        total_computers += 1

    
    print(f"People: {len(result)}")
    print(f"Rows processed: {total_rows}")
    print(f"Computers assigned: {total_computers}")
    print(f"Skipped {skipped} rows (missing names)")
    
    # Save to JSON
    print(f"Saving to: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("✅ Extraction complete!")
    
    # Show sample of extracted names
    if result:
        print(f"\nSample names extracted:")
        for i, name in enumerate(sorted(result.keys())[:10]):
            computers = list(result[name].keys())
            preview = ", ".join(computers[:3]) + (" ..." if len(computers) > 3 else "")
            print(f"  {i+1:2d}. {name} -> {len(computers)} computer(s): {preview}")
        if len(result) > 10:
            print(f"  ... and {len(result) - 10} more")


def main():
    """Main function."""
    # Default paths
    default_excel = "EA_US_Desktop_Hardware_GPU_Master List_2025.xlsx"
    default_json = "gpu_data_by_name.json"
    
    # Parse arguments
    if len(sys.argv) >= 3:
        excel_path = sys.argv[1]
        output_path = sys.argv[2]
    elif len(sys.argv) == 2:
        excel_path = sys.argv[1]
        output_path = default_json
    else:
        excel_path = default_excel
        output_path = default_json
    
    # Check if input file exists
    if not os.path.exists(excel_path):
        print(f"ERROR: Input file not found: {excel_path}")
        print(f"Usage: python {sys.argv[0]} [input_excel] [output_json]")
        return 1
    
    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    try:
        extract_gpu_data(excel_path, output_path)
        return 0
    except Exception as e:
        print(f"ERROR: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
