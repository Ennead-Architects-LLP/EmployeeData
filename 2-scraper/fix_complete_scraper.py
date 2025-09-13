#!/usr/bin/env python3
"""
Script to fix the broken complete_scraper.py by removing orphaned parallel processing code
"""

def fix_complete_scraper():
    """Remove orphaned parallel processing code from complete_scraper.py"""
    
    # Read the file
    with open('src/core/complete_scraper.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the problematic section and remove it
    new_lines = []
    skip = False
    removed_lines = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Start skipping when we hit the orphaned code (around line 1889)
        if (line_num >= 1889 and 
            ('self.logger.info("[START] Initializing Playwright browser...")' in line or 
             line.strip().startswith('self.logger.info("[START]') or
             'async with self.performance_monitor.track_operation' in line)):
            skip = True
            removed_lines += 1
            continue
        
        # Stop skipping when we hit the next proper method
        if skip and line.strip().startswith('async def scrape_all_employees_incremental'):
            skip = False
            new_lines.append(line)
            continue
        
        # If we're not skipping, add the line
        if not skip:
            new_lines.append(line)
        else:
            removed_lines += 1
    
    # Write the cleaned content
    with open('src/core/complete_scraper.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f'✅ Fixed complete_scraper.py - removed {removed_lines} lines of orphaned code')
    print(f'✅ File now has {len(new_lines)} lines (was {len(lines)} lines)')

if __name__ == "__main__":
    fix_complete_scraper()
