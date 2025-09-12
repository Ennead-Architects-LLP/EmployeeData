# Excel to JSON Merger

This standalone script processes 3 Excel files and creates a composite JSON file with employee information linked by human names as keys.

## Files Required

1. `Employee List .xlsx` - Basic employee information (First Name, Last Name, Company, Office, etc.)
2. `GPU by User.xlsx` - Computer/GPU specifications per user
3. `Master Technology List.xlsx` - Employee roles, titles, and office locations

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python excel_to_json_merger.py
```

## Output

The script generates `composite_employees.json` with the following structure:

```json
{
  "summary": {
    "total_employees": 216,
    "employees_with_computers": 52,
    "total_computers": 53,
    "employees_with_roles": 109,
    "generation_timestamp": "2025-09-12T15:08:33.682535"
  },
  "employees": {
    "Employee Name": {
      "full_name": "Employee Name",
      "first_name": "First",
      "last_name": "Last",
      "preferred_name": "",
      "company": "Company Name",
      "office": "Office Location",
      "computers": [
        {
          "computername": "COMPUTER-NAME",
          "username": "username",
          "os": "Operating System",
          "manufacturer": "Manufacturer",
          "model": "Model",
          "total_physical_memory": 16777216.0,
          "cpu": "CPU Model",
          "serial_number": "Serial Number",
          "gpu_name": "GPU Name",
          "gpu_processor": "GPU Processor",
          "gpu_driver": "GPU Driver Version",
          "gpu_memory": 4193280.0,
          "date": "2025-06-27T15:26:00"
        }
      ],
      "role": "Job Role",
      "title": "Job Title",
      "office_location": "Office Location"
    }
  }
}
```

## Key Features

- **Human names as keys**: Each employee is identified by their full name
- **Multiple computers support**: Employees can have multiple computers stored as a list
- **Enhanced fuzzy name matching**: Advanced matching with multiple algorithms:
  - Handles spelling variations and typos
  - Supports common nicknames (Bob/Robert, Mike/Michael, etc.)
  - Token-based matching for different name orders
  - Configurable similarity thresholds
- **Comprehensive data linking**: Combines information from all 3 Excel files
- **Data quality monitoring**: Automatic alerts for data loss and missing information
- **Detailed reporting**: Shows unmatched records and data coverage statistics
- **Standalone operation**: No dependencies on the rest of the repository
- **Intelligent matching**: Uses best-match scoring to avoid duplicate entries

## Data Sources

- **Employee List**: Basic employee information and office assignments
- **GPU by User**: Detailed computer specifications including hardware, OS, and GPU details
- **Master Technology List**: Job roles, titles, and office locations

## Data Quality Monitoring

The script automatically monitors data quality and provides comprehensive alerts for:

### Coverage Alerts
- **Low coverage**: Warns when less than 30% of employees have computer data
- **Missing roles**: Alerts when less than 50% have role information  
- **Missing titles**: Warns when less than 40% have title information
- **Critical gaps**: Flags when less than 20% have complete data from all sources

### Data Loss Alerts
- **Invalid names**: Tracks records with empty, null, or invalid names
- **Data loss by source**: Reports exactly how many records were lost from each Excel file
- **Unmatched records**: Reports records that couldn't be matched between files

### Matching Quality Alerts
- **Low confidence matches**: Flags matches with <90% confidence that may be incorrect
- **Mismatch detection**: Shows potential name mismatches with confidence scores
- **Duplicate prevention**: Tracks when multiple records might match the same employee

## Notes

- **Enhanced matching**: The script uses multiple fuzzy matching algorithms to handle:
  - Spelling variations and typos
  - Common nicknames and shortened names
  - Different name orders (Last, First vs First Last)
  - Middle name variations
- **Smart scoring**: Uses best-match scoring to prevent duplicate entries
- **Fallback handling**: Employees without computer data will have an empty computers array
- **Data expansion**: Creates new entries for employees found in GPU or Tech lists but not in the Employee List
- **Data normalization**: All data is cleaned and normalized during processing
- **Threshold tuning**: Matching threshold can be adjusted (default: 75% similarity)
- **Quality reporting**: Detailed reports show exactly which data is missing and why
