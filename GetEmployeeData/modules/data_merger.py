"""
Data merger for combining employee data from multiple sources.

This module merges data from the main employee scraper with seating chart data.
"""

import logging
from typing import List, Tuple, Optional
from .employee_data import EmployeeData
from .seating_chart_scraper import SeatingChartData


class DataMerger:
    """Merges employee data from multiple sources."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def merge_employee_data(self, employees: List[EmployeeData], seating_data: Optional[List] = None) -> List[EmployeeData]:
        """
        Merge seating chart data with existing employee data.
        
        Args:
            employees: List of EmployeeData objects
            seating_data: List of SeatingChartData objects
            
        Returns:
            Updated list of EmployeeData objects
        """
        if not seating_data:
            self.logger.info("No seating data provided - returning employees unchanged")
            return employees
            
        self.logger.info(f"Merging {len(employees)} employees with {len(seating_data)} seating records")
        
        # Create a lookup dictionary for seating data
        seating_lookup = {}
        for seat_data in seating_data:
            # Try multiple name variations for matching
            name_variations = self._generate_name_variations(seat_data.name)
            for variation in name_variations:
                seating_lookup[variation.lower()] = seat_data
        
        merged_count = 0
        for employee in employees:
            if not employee.real_name:
                continue
                
            # Try to find matching seating data
            employee_name_variations = self._generate_name_variations(employee.real_name)
            
            for variation in employee_name_variations:
                if variation.lower() in seating_lookup:
                    seat_data = seating_lookup[variation.lower()]
                    self._merge_single_employee(employee, seat_data)
                    merged_count += 1
                    break
        
        self.logger.info(f"Successfully merged {merged_count} employees with seating data")
        return employees
    
    def _generate_name_variations(self, name: str) -> List[str]:
        """Generate name variations for better matching."""
        if not name:
            return []
        
        variations = [name]
        
        # Split into parts
        parts = name.split()
        if len(parts) >= 2:
            # First Last
            variations.append(f"{parts[0]} {parts[-1]}")
            # Last, First
            variations.append(f"{parts[-1]}, {parts[0]}")
            # First Last (no middle)
            if len(parts) > 2:
                variations.append(f"{parts[0]} {parts[-1]}")
        
        return variations
    
    def _merge_single_employee(self, employee: EmployeeData, seat_data):
        """Merge seating data into a single employee record."""
        # Update department if not already set or if seating data is more specific
        if seat_data.department and (not employee.department or len(seat_data.department) > len(employee.department)):
            employee.department = seat_data.department
        
        # Add seat assignment
        if seat_data.seat:
            employee.seat_assignment = seat_data.seat
        
        # Update office location if not already set
        if seat_data.office_location and not employee.office_location:
            employee.office_location = seat_data.office_location
    
    def find_unmatched_employees(self, employees: List[EmployeeData], seating_data: Optional[List] = None) -> Tuple[List[EmployeeData], List]:
        """
        Find employees and seating data that couldn't be matched.
        
        Returns:
            Tuple of (unmatched_employees, unmatched_seating_data)
        """
        if not seating_data:
            return employees, []
            
        # Create lookup for seating data
        seating_lookup = {}
        for seat_data in seating_data:
            name_variations = self._generate_name_variations(seat_data.name)
            for variation in name_variations:
                seating_lookup[variation.lower()] = seat_data
        
        unmatched_employees = []
        matched_seating = set()
        
        for employee in employees:
            if not employee.real_name:
                unmatched_employees.append(employee)
                continue
            
            employee_name_variations = self._generate_name_variations(employee.real_name)
            matched = False
            
            for variation in employee_name_variations:
                if variation.lower() in seating_lookup:
                    matched_seating.add(seating_lookup[variation.lower()])
                    matched = True
                    break
            
            if not matched:
                unmatched_employees.append(employee)
        
        unmatched_seating = [seat_data for seat_data in seating_data if seat_data not in matched_seating]
        
        return unmatched_employees, unmatched_seating
