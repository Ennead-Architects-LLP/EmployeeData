#!/usr/bin/env python3
"""
Excel to JSON Merger
====================

This script processes 3 Excel files and creates a composite JSON file
with employee information linked by human names as keys.

Files processed:
1. Employee List .xlsx - Basic employee information
2. GPU by User.xlsx - Computer/GPU specifications per user
3. Master Technology List.xlsx - Employee roles and titles

Output: composite_employees.json
"""

import pandas as pd
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from fuzzywuzzy import fuzz, process

class ExcelToJsonMerger:
    def __init__(self):
        self.employee_data = {}
        self.unmatched_records = {
            'gpu_records': [],
            'tech_records': []
        }
        self.data_quality_issues = []
        self.mismatch_alerts = []
        self.invalid_names = []
        self.data_loss_summary = {
            'gpu_data_lost': 0,
            'tech_data_lost': 0,
            'employee_data_lost': 0
        }
        
    def normalize_name(self, name: str, source: str = "unknown") -> str:
        """Normalize names for consistent matching"""
        if pd.isna(name) or name == 'Name':
            self.invalid_names.append({
                'original_name': str(name) if not pd.isna(name) else 'NaN',
                'source': source,
                'reason': 'Empty or header name'
            })
            return ""
        
        # Convert to string and clean
        original_name = str(name).strip()
        name = original_name
        
        # Check for obviously invalid names
        if len(name) < 2 or name.lower() in ['nan', 'none', 'null', '']:
            self.invalid_names.append({
                'original_name': original_name,
                'source': source,
                'reason': 'Too short or invalid value'
            })
            return ""
        
        # Remove extra spaces and normalize
        name = re.sub(r'\s+', ' ', name)
        
        # Handle special cases like "Feder, AJ" -> "AJ Feder"
        if ',' in name:
            parts = name.split(',')
            if len(parts) == 2:
                last, first = parts[0].strip(), parts[1].strip()
                name = f"{first} {last}"
        
        # Final validation
        if len(name) < 2 or not any(c.isalpha() for c in name):
            self.invalid_names.append({
                'original_name': original_name,
                'source': source,
                'reason': 'No alphabetic characters'
            })
            return ""
        
        return name.title()
    
    def create_full_name(self, first: str, last: str) -> str:
        """Create full name from first and last name"""
        if pd.isna(first) or pd.isna(last):
            return ""
        
        first = str(first).strip()
        last = str(last).strip()
        
        # Remove extra spaces
        first = re.sub(r'\s+', ' ', first)
        last = re.sub(r'\s+', ' ', last)
        
        return f"{first} {last}".title()
    
    def load_employee_list(self, filepath: str):
        """Load employee list data and merge with existing base"""
        print("Loading Employee List and merging with base data...")
        df = pd.read_excel(filepath)
        
        matched_count = 0
        new_count = 0
        
        for _, row in df.iterrows():
            if pd.isna(row['First Name']) or pd.isna(row['Last Name']):
                self.data_loss_summary['employee_data_lost'] += 1
                continue
                
            full_name = self.create_full_name(row['First Name'], row['Last Name'])
            if not full_name:
                self.data_loss_summary['employee_data_lost'] += 1
                continue
                
            # Clean office name
            office = str(row['Office']).strip() if not pd.isna(row['Office']) else ""
            
            # Try to find matching employee in existing base
            found_match = False
            best_match = None
            best_score = 0
            
            for emp_name, emp_data in self.employee_data.items():
                if self.names_match(full_name, emp_name, threshold=75):
                    # Calculate match score for ranking
                    score = fuzz.token_sort_ratio(full_name, emp_name)
                    if score > best_score:
                        best_score = score
                        best_match = emp_name
            
            if best_match:
                # Update existing employee with basic info
                self.employee_data[best_match]['first_name'] = str(row['First Name']).strip()
                self.employee_data[best_match]['last_name'] = str(row['Last Name']).strip()
                self.employee_data[best_match]['preferred_name'] = str(row['Preferred Name']).strip() if not pd.isna(row['Preferred Name']) else ""
                self.employee_data[best_match]['company'] = str(row['Company']).strip() if not pd.isna(row['Company']) else ""
                self.employee_data[best_match]['office'] = office
                found_match = True
                matched_count += 1
                
                # Track potential mismatches (low confidence matches)
                if best_score < 90:
                    self.mismatch_alerts.append({
                        'type': 'Low confidence match',
                        'source': 'Employee List',
                        'original_name': full_name,
                        'matched_name': best_match,
                        'confidence_score': best_score,
                        'reason': f'Matched with {best_score}% confidence - may be incorrect'
                    })
            else:
                # Create new entry for employee not in tech list
                self.employee_data[full_name] = {
                    'full_name': full_name,
                    'first_name': str(row['First Name']).strip(),
                    'last_name': str(row['Last Name']).strip(),
                    'preferred_name': str(row['Preferred Name']).strip() if not pd.isna(row['Preferred Name']) else "",
                    'company': str(row['Company']).strip() if not pd.isna(row['Company']) else "",
                    'office': office,
                    'computers': [],
                    'role': "",
                    'title': "",
                    'office_location': ""
                }
                new_count += 1
                # Track as unmatched from tech list
                self.unmatched_records['tech_records'].append({
                    'name': full_name,
                    'role': '',
                    'title': '',
                    'reason': 'Found in Employee List but not in Master Tech List'
                })
        
        print(f"Matched {matched_count} employees from Employee List to existing base")
        print(f"Added {new_count} new employees from Employee List")
        print(f"Total employees now: {len(self.employee_data)}")
    
    def load_gpu_data(self, filepath: str):
        """Load GPU/computer data and merge with existing base"""
        print("Loading GPU by User data and merging with base...")
        df = pd.read_excel(filepath)
        
        gpu_count = 0
        matched_count = 0
        new_count = 0
        
        for _, row in df.iterrows():
            # Try to get name first, then fallback to username
            name_to_use = None
            name_source = None
            
            if not pd.isna(row['Name']) and str(row['Name']).strip():
                normalized_name = self.normalize_name(row['Name'], 'GPU by User')
                if normalized_name:
                    name_to_use = normalized_name
                    name_source = 'Name'
            elif not pd.isna(row['Username']) and str(row['Username']).strip():
                # Use username as backup
                username = str(row['Username']).strip()
                name_to_use = username
                name_source = 'Username'
            
            if not name_to_use:
                self.data_loss_summary['gpu_data_lost'] += 1
                continue
                
            gpu_count += 1
            
            # Create computer specification dictionary
            computer_spec = {
                'computername': str(row['Computername']).strip() if not pd.isna(row['Computername']) else "",
                'username': str(row['Username']).strip() if not pd.isna(row['Username']) else "",
                'os': str(row['OS']).strip() if not pd.isna(row['OS']) else "",
                'manufacturer': str(row['Manufacturer']).strip() if not pd.isna(row['Manufacturer']) else "",
                'model': str(row['Model']).strip() if not pd.isna(row['Model']) else "",
                'total_physical_memory': float(row['Total Physical Memory']) if not pd.isna(row['Total Physical Memory']) else 0,
                'cpu': str(row['CPU']).strip() if not pd.isna(row['CPU']) else "",
                'serial_number': str(row['Serial Number']).strip() if not pd.isna(row['Serial Number']) else "",
                'gpu_name': str(row['GPU Name']).strip() if not pd.isna(row['GPU Name']) else "",
                'gpu_processor': str(row['GPU Processor']).strip() if not pd.isna(row['GPU Processor']) else "",
                'gpu_driver': str(row['GPU Driver']).strip() if not pd.isna(row['GPU Driver']) else "",
                'gpu_memory': float(row['GPU Memory']) if not pd.isna(row['GPU Memory']) else 0,
                'date': row['Date'].isoformat() if not pd.isna(row['Date']) else ""
            }
            
            # Try to find matching employee in existing base
            found_match = False
            best_match = None
            best_score = 0
            
            for emp_name, emp_data in self.employee_data.items():
                # Try matching with the name we're using (could be Name or Username)
                if self.names_match(name_to_use, emp_name, threshold=75):
                    # Calculate match score for ranking
                    score = fuzz.token_sort_ratio(name_to_use, emp_name)
                    if score > best_score:
                        best_score = score
                        best_match = emp_name
                
                # If we're using a username, also try matching against employee usernames
                if name_source == 'Username':
                    # Check if any employee has this username in their computer specs
                    for comp in emp_data.get('computers', []):
                        if comp.get('username', '').lower() == name_to_use.lower():
                            score = 100  # Exact username match
                            if score > best_score:
                                best_score = score
                                best_match = emp_name
                                break
            
            if best_match:
                # Add computer to existing employee
                self.employee_data[best_match]['computers'].append(computer_spec)
                found_match = True
                matched_count += 1
                
                # Track potential mismatches (low confidence matches)
                if best_score < 90:
                    self.mismatch_alerts.append({
                        'type': 'Low confidence match',
                        'source': f'GPU by User ({name_source})',
                        'original_name': name_to_use,
                        'matched_name': best_match,
                        'confidence_score': best_score,
                        'reason': f'Matched with {best_score}% confidence - may be incorrect'
                    })
            else:
                # Create new entry for employee not in base
                self.employee_data[name_to_use] = {
                    'full_name': name_to_use,
                    'first_name': "",
                    'last_name': "",
                    'preferred_name': "",
                    'company': "",
                    'office': "",
                    'computers': [computer_spec],
                    'role': "",
                    'title': "",
                    'office_location': ""
                }
                new_count += 1
                # Track as unmatched from base
                self.unmatched_records['gpu_records'].append({
                    'name': name_to_use,
                    'computername': computer_spec['computername'],
                    'reason': f'Found in GPU data ({name_source}) but not in base dataset'
                })
        
        print(f"Matched {matched_count} GPU records to existing employees")
        print(f"Added {new_count} new employees from GPU data")
        print(f"Total employees now: {len(self.employee_data)}")
    
    def load_master_tech_list(self, filepath: str):
        """Load master technology list data as the base dataset"""
        print("Loading Master Technology List as base dataset...")
        df = pd.read_excel(filepath, header=1)  # Use row 2 (index 1) as header
        
        tech_count = 0
        
        for _, row in df.iterrows():
            if pd.isna(row['Name']) or row['Name'] == 'Name':
                continue
                
            normalized_name = self.normalize_name(row['Name'], 'Master Tech List')
            if not normalized_name:
                self.data_loss_summary['tech_data_lost'] += 1
                continue
                
            tech_count += 1
            
            role = str(row['Role']).strip() if not pd.isna(row['Role']) else ""
            title = str(row['Title']).strip() if not pd.isna(row['Title']) else ""
            office_location = str(row['Office Location']).strip() if not pd.isna(row['Office Location']) else ""
            
            # Create base employee entry with tech data
            self.employee_data[normalized_name] = {
                'full_name': normalized_name,
                'first_name': "",
                'last_name': "",
                'preferred_name': "",
                'company': "",
                'office': "",
                'computers': [],
                'role': role,
                'title': title,
                'office_location': office_location
            }
        
        print(f"Created base dataset with {tech_count} employees from Master Technology List")
    
    def names_match(self, name1: str, name2: str, threshold: int = 85) -> bool:
        """Check if two names match using fuzzy matching"""
        if not name1 or not name2:
            return False
        
        # Normalize both names
        n1 = self.normalize_name(name1)
        n2 = self.normalize_name(name2)
        
        if not n1 or not n2:
            return False
        
        # Exact match
        if n1.lower() == n2.lower():
            return True
        
        # Use fuzzywuzzy for better matching
        # Try different matching strategies
        ratios = [
            fuzz.ratio(n1, n2),
            fuzz.partial_ratio(n1, n2),
            fuzz.token_sort_ratio(n1, n2),
            fuzz.token_set_ratio(n1, n2)
        ]
        
        # Use the best ratio
        best_ratio = max(ratios)
        
        # Also check if one name is contained in the other (for nicknames)
        if n1.lower() in n2.lower() or n2.lower() in n1.lower():
            return True
        
        # Check for common nickname patterns
        if self.check_nickname_match(n1, n2):
            return True
        
        return best_ratio >= threshold
    
    def check_nickname_match(self, name1: str, name2: str) -> bool:
        """Check for common nickname patterns"""
        # Common nickname mappings
        nicknames = {
            'robert': ['bob', 'rob', 'bobby'],
            'richard': ['rick', 'dick', 'rich'],
            'william': ['will', 'bill', 'billy'],
            'michael': ['mike', 'mick'],
            'david': ['dave', 'davey'],
            'christopher': ['chris', 'christy'],
            'daniel': ['dan', 'danny'],
            'matthew': ['matt', 'matty'],
            'anthony': ['tony', 'ant'],
            'andrew': ['andy', 'drew'],
            'joseph': ['joe', 'joey'],
            'james': ['jim', 'jimmy', 'jamie'],
            'charles': ['charlie', 'chuck'],
            'thomas': ['tom', 'tommy'],
            'alexander': ['alex', 'al'],
            'benjamin': ['ben', 'benny'],
            'samuel': ['sam', 'sammy'],
            'jonathan': ['jon', 'johnny'],
            'nicholas': ['nick', 'nicky'],
            'timothy': ['tim', 'timmy'],
            'jennifer': ['jen', 'jenny'],
            'elizabeth': ['liz', 'beth', 'betty'],
            'patricia': ['pat', 'patty', 'tricia'],
            'jessica': ['jess', 'jessie'],
            'sarah': ['sally', 'sara'],
            'michelle': ['mich', 'shell'],
            'stephanie': ['steph', 'stephie'],
            'katherine': ['kate', 'katie', 'kat'],
            'christina': ['chris', 'christy'],
            'amanda': ['mandy', 'mandi']
        }
        
        # Normalize names for comparison
        n1_parts = name1.lower().split()
        n2_parts = name2.lower().split()
        
        # Check if any part of name1 matches a nickname of any part of name2
        for part1 in n1_parts:
            for part2 in n2_parts:
                if part1 in nicknames and part2 in nicknames[part1]:
                    return True
                if part2 in nicknames and part1 in nicknames[part2]:
                    return True
        
        return False
    
    def find_best_match(self, target_name: str, candidate_names: List[str], threshold: int = 80) -> Optional[str]:
        """Find the best matching name from a list of candidates"""
        if not target_name or not candidate_names:
            return None
        
        # Use fuzzywuzzy's process.extractOne for best match
        result = process.extractOne(target_name, candidate_names, scorer=fuzz.token_sort_ratio)
        
        if result and result[1] >= threshold:
            return result[0]
        
        return None
    
    def generate_summary(self) -> Dict[str, Any]:
        """Generate summary statistics with data quality alerts"""
        total_employees = len(self.employee_data)
        employees_with_computers = sum(1 for emp in self.employee_data.values() if emp['computers'])
        total_computers = sum(len(emp['computers']) for emp in self.employee_data.values())
        employees_with_roles = sum(1 for emp in self.employee_data.values() if emp['role'])
        employees_with_titles = sum(1 for emp in self.employee_data.values() if emp['title'])
        employees_with_complete_data = sum(1 for emp in self.employee_data.values() 
                                         if emp['computers'] and emp['role'] and emp['first_name'])
        
        # Calculate data completeness percentages
        computer_coverage = (employees_with_computers / total_employees * 100) if total_employees > 0 else 0
        role_coverage = (employees_with_roles / total_employees * 100) if total_employees > 0 else 0
        title_coverage = (employees_with_titles / total_employees * 100) if total_employees > 0 else 0
        complete_data_coverage = (employees_with_complete_data / total_employees * 100) if total_employees > 0 else 0
        
        # Generate alerts for data quality issues
        alerts = []
        
        if computer_coverage < 30:
            alerts.append(f"⚠️  LOW COMPUTER COVERAGE: Only {computer_coverage:.1f}% of employees have computer data")
        
        if role_coverage < 50:
            alerts.append(f"⚠️  LOW ROLE COVERAGE: Only {role_coverage:.1f}% of employees have role information")
        
        if title_coverage < 40:
            alerts.append(f"⚠️  LOW TITLE COVERAGE: Only {title_coverage:.1f}% of employees have title information")
        
        if complete_data_coverage < 20:
            alerts.append(f"🚨 CRITICAL: Only {complete_data_coverage:.1f}% of employees have complete data from all sources")
        
        # Check for potential data loss
        employees_without_any_tech_data = sum(1 for emp in self.employee_data.values() 
                                            if not emp['computers'] and not emp['role'] and not emp['title'])
        
        if employees_without_any_tech_data > total_employees * 0.3:
            alerts.append(f"🚨 HIGH DATA LOSS: {employees_without_any_tech_data} employees ({employees_without_any_tech_data/total_employees*100:.1f}%) have no technology data")
        
        # Check for unmatched records
        unmatched_gpu = len(self.unmatched_records['gpu_records'])
        unmatched_tech = len(self.unmatched_records['tech_records'])
        
        if unmatched_gpu > 0:
            alerts.append(f"⚠️  UNMATCHED GPU RECORDS: {unmatched_gpu} computer records couldn't be matched to Employee List")
        
        if unmatched_tech > 0:
            alerts.append(f"⚠️  UNMATCHED TECH RECORDS: {unmatched_tech} technology records couldn't be matched to Employee List")
        
        # Add data loss alerts
        if self.data_loss_summary['gpu_data_lost'] > 0:
            alerts.append(f"🚨 DATA LOSS: {self.data_loss_summary['gpu_data_lost']} GPU records lost due to invalid names")
        
        if self.data_loss_summary['tech_data_lost'] > 0:
            alerts.append(f"🚨 DATA LOSS: {self.data_loss_summary['tech_data_lost']} tech records lost due to invalid names")
        
        if self.data_loss_summary['employee_data_lost'] > 0:
            alerts.append(f"🚨 DATA LOSS: {self.data_loss_summary['employee_data_lost']} employee records lost due to invalid names")
        
        # Add mismatch alerts
        if self.mismatch_alerts:
            alerts.append(f"⚠️  LOW CONFIDENCE MATCHES: {len(self.mismatch_alerts)} matches with <90% confidence")
        
        # Add invalid name alerts
        if self.invalid_names:
            alerts.append(f"🚨 INVALID NAMES: {len(self.invalid_names)} records with invalid or empty names")
        
        return {
            'total_employees': total_employees,
            'employees_with_computers': employees_with_computers,
            'total_computers': total_computers,
            'employees_with_roles': employees_with_roles,
            'employees_with_titles': employees_with_titles,
            'employees_with_complete_data': employees_with_complete_data,
            'data_coverage': {
                'computer_coverage_percent': round(computer_coverage, 1),
                'role_coverage_percent': round(role_coverage, 1),
                'title_coverage_percent': round(title_coverage, 1),
                'complete_data_coverage_percent': round(complete_data_coverage, 1)
            },
            'unmatched_records': {
                'gpu_records_count': unmatched_gpu,
                'tech_records_count': unmatched_tech,
                'gpu_records': self.unmatched_records['gpu_records'][:10],  # Show first 10 for debugging
                'tech_records': self.unmatched_records['tech_records'][:10]  # Show first 10 for debugging
            },
            'data_loss_summary': self.data_loss_summary,
            'mismatch_alerts': self.mismatch_alerts[:20],  # Show first 20 for debugging
            'invalid_names': self.invalid_names[:20],  # Show first 20 for debugging
            'alerts': alerts,
            'matching_algorithm': 'Enhanced fuzzy matching with nickname support',
            'generation_timestamp': datetime.now().isoformat()
        }
    
    def save_json(self, output_file: str):
        """Save the composite data to JSON file"""
        print(f"Saving composite data to {output_file}...")
        
        # Add summary to the data
        composite_data = {
            'summary': self.generate_summary(),
            'employees': self.employee_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(composite_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully saved {len(self.employee_data)} employees to {output_file}")
    
    def process_all_files(self, employee_file: str, gpu_file: str, tech_file: str, output_file: str):
        """Process all Excel files and generate composite JSON"""
        print("Starting Excel to JSON merger process...")
        print("=" * 50)
        print("Using Master Technology List as base (186 names)")
        print("Then merging Employee List and GPU data...")
        print("=" * 50)
        
        # Load data in order: Tech List (base) -> Employee List -> GPU data
        self.load_master_tech_list(tech_file)
        self.load_employee_list(employee_file)
        self.load_gpu_data(gpu_file)
        
        # Save composite JSON
        self.save_json(output_file)
        
        # Print summary with alerts
        summary = self.generate_summary()
        print("\n" + "=" * 50)
        print("PROCESSING SUMMARY")
        print("=" * 50)
        print(f"Total employees: {summary['total_employees']}")
        print(f"Employees with computers: {summary['employees_with_computers']}")
        print(f"Total computers: {summary['total_computers']}")
        print(f"Employees with roles: {summary['employees_with_roles']}")
        print(f"Employees with titles: {summary['employees_with_titles']}")
        print(f"Employees with complete data: {summary['employees_with_complete_data']}")
        
        # Display data coverage
        coverage = summary['data_coverage']
        print(f"\nData Coverage:")
        print(f"  Computer data: {coverage['computer_coverage_percent']}%")
        print(f"  Role data: {coverage['role_coverage_percent']}%")
        print(f"  Title data: {coverage['title_coverage_percent']}%")
        print(f"  Complete data: {coverage['complete_data_coverage_percent']}%")
        
        # Display alerts prominently
        if summary['alerts']:
            print(f"\n" + "🚨" * 20)
            print("DATA QUALITY ALERTS")
            print("🚨" * 20)
            for alert in summary['alerts']:
                print(alert)
            print("🚨" * 20)
        
        # Display unmatched records summary
        unmatched = summary['unmatched_records']
        if unmatched['gpu_records_count'] > 0 or unmatched['tech_records_count'] > 0:
            print(f"\nUnmatched Records:")
            print(f"  GPU records: {unmatched['gpu_records_count']}")
            print(f"  Tech records: {unmatched['tech_records_count']}")
        
        print(f"\nOutput file: {output_file}")
        
        # Generate detailed data quality report
        self.generate_data_quality_report()

    def generate_data_quality_report(self):
        """Generate a detailed data quality report"""
        print(f"\n" + "=" * 50)
        print("DETAILED DATA QUALITY REPORT")
        print("=" * 50)
        
        # Analyze employees with missing data
        employees_missing_computer = [name for name, emp in self.employee_data.items() 
                                    if not emp['computers'] and emp['first_name']]
        employees_missing_role = [name for name, emp in self.employee_data.items() 
                                if not emp['role'] and emp['first_name']]
        employees_missing_title = [name for name, emp in self.employee_data.items() 
                                 if not emp['title'] and emp['first_name']]
        
        print(f"\nEmployees from Employee List missing data:")
        print(f"  Missing computer data: {len(employees_missing_computer)}")
        print(f"  Missing role data: {len(employees_missing_role)}")
        print(f"  Missing title data: {len(employees_missing_title)}")
        
        # Show sample of employees with missing data
        if employees_missing_computer:
            print(f"\nSample employees missing computer data:")
            for name in employees_missing_computer[:5]:
                print(f"  - {name}")
        
        if employees_missing_role:
            print(f"\nSample employees missing role data:")
            for name in employees_missing_role[:5]:
                print(f"  - {name}")
        
        # Show unmatched records details
        if self.unmatched_records['gpu_records']:
            print(f"\nSample unmatched GPU records:")
            for record in self.unmatched_records['gpu_records'][:5]:
                print(f"  - {record['name']} (Computer: {record['computername']})")
        
        if self.unmatched_records['tech_records']:
            print(f"\nSample unmatched tech records:")
            for record in self.unmatched_records['tech_records'][:5]:
                print(f"  - {record['name']} (Role: {record['role']}, Title: {record['title']})")
        
        # Show data loss details
        print(f"\nData Loss Summary:")
        print(f"  GPU data lost: {self.data_loss_summary['gpu_data_lost']} records")
        print(f"  Tech data lost: {self.data_loss_summary['tech_data_lost']} records")
        print(f"  Employee data lost: {self.data_loss_summary['employee_data_lost']} records")
        
        # Show mismatch alerts
        if self.mismatch_alerts:
            print(f"\nLow Confidence Matches ({len(self.mismatch_alerts)} total):")
            for alert in self.mismatch_alerts[:5]:
                print(f"  - {alert['source']}: '{alert['original_name']}' -> '{alert['matched_name']}' ({alert['confidence_score']}%)")
        
        # Show invalid names
        if self.invalid_names:
            print(f"\nInvalid Names ({len(self.invalid_names)} total):")
            for invalid in self.invalid_names[:5]:
                print(f"  - {invalid['source']}: '{invalid['original_name']}' ({invalid['reason']})")
        
        print(f"\n" + "=" * 50)

def main():
    """Main function"""
    merger = ExcelToJsonMerger()
    
    # File paths
    employee_file = "Employee List .xlsx"
    gpu_file = "GPU by User.xlsx"
    tech_file = "Master Technology List.xlsx"
    output_file = "composite_employees.json"
    
    # Process all files
    merger.process_all_files(employee_file, gpu_file, tech_file, output_file)

if __name__ == "__main__":
    main()
