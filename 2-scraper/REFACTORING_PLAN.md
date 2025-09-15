# Scraper Refactoring Plan

## 🚨 Problem: Code Duplication

Both `SimpleEmployeeScraper` and `CompleteScraper` extract the same core employee data fields, creating:
- **Code duplication** - Same logic in two places
- **Inconsistency risk** - Different implementations might produce different results
- **Maintenance burden** - Changes need to be made in two places
- **Testing complexity** - Need to test both scrapers separately

## 🎯 Solution: Shared Base Scraper

### 1. Create BaseEmployeeScraper
- ✅ **Created**: `src/core/base_scraper.py`
- **Purpose**: Contains shared core functionality for basic employee data extraction
- **Features**: 
  - Consistent selectors
  - Standardized data extraction
  - Image downloading
  - Data validation
  - Location normalization

### 2. Refactor SimpleEmployeeScraper
**Current**: Extracts basic data directly
**New**: Inherits from BaseEmployeeScraper + adds simple-specific features

```python
class SimpleEmployeeScraper(BaseEmployeeScraper):
    def __init__(self, ...):
        super().__init__(download_images, timeout)
        # Simple-specific initialization
    
    async def scrape_employee_profile(self, ...):
        # Use parent's extract_basic_employee_data()
        employee = await self.extract_basic_employee_data(page, profile_url, name, image_url)
        # Add any simple-specific processing
        return employee
```

### 3. Refactor CompleteScraper
**Current**: Extracts basic data + advanced data
**New**: Inherits from BaseEmployeeScraper + adds advanced features

```python
class CompleteScraper(BaseEmployeeScraper):
    def __init__(self, ...):
        super().__init__(download_images, timeout)
        # Complete-specific initialization (projects, seating, etc.)
    
    async def scrape_employee_profile(self, ...):
        # Use parent's extract_basic_employee_data()
        employee = await self.extract_basic_employee_data(page, profile_url, name, image_url)
        # Add advanced data extraction (projects, education, etc.)
        await self._extract_projects(page, employee)
        await self._extract_education(page, employee)
        # ... other advanced features
        return employee
```

## 📊 Benefits

### ✅ Consistency
- **Same selectors** for basic data across both scrapers
- **Same validation** logic
- **Same data format** output

### ✅ Maintainability
- **Single source of truth** for basic data extraction
- **Changes in one place** affect both scrapers
- **Easier testing** - test base functionality once

### ✅ Reliability
- **Proven logic** shared between scrapers
- **Reduced bugs** from duplicate code
- **Consistent behavior** in production

## 🧪 Testing Strategy

### 1. Unit Tests
- Test `BaseEmployeeScraper` functionality
- Test data validation and normalization
- Test selector consistency

### 2. Integration Tests
- Run both scrapers on same employee
- Compare outputs for basic fields
- Verify advanced fields only in CompleteScraper

### 3. Regression Tests
- Ensure existing functionality still works
- Verify no data loss during refactoring

## 📋 Implementation Steps

### Phase 1: Base Scraper (✅ Complete)
- [x] Create `BaseEmployeeScraper`
- [x] Implement shared core functionality
- [x] Add data validation and normalization
- [x] Create test script

### Phase 2: Refactor SimpleEmployeeScraper
- [ ] Update imports and inheritance
- [ ] Remove duplicate code
- [ ] Update method calls to use base class
- [ ] Test functionality

### Phase 3: Refactor CompleteScraper
- [ ] Update imports and inheritance
- [ ] Remove duplicate basic data extraction
- [ ] Keep advanced features
- [ ] Test functionality

### Phase 4: Integration Testing
- [ ] Run both scrapers on test data
- [ ] Compare outputs for consistency
- [ ] Verify no regressions
- [ ] Update documentation

## 🎯 Expected Results

After refactoring:
- **50% less code** in SimpleEmployeeScraper
- **30% less code** in CompleteScraper
- **100% consistency** for basic data fields
- **Easier maintenance** and testing
- **Same functionality** with better architecture

## 🔍 Verification

To verify both scrapers produce the same results:

```bash
cd 2-scraper
python test_scraper_consistency.py
```

This will show:
- Field-by-field comparison
- Identical basic data extraction
- Differences only in advanced features
- Validation of shared functionality
