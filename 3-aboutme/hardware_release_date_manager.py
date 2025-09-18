"""
Hardware Release Date Manager

A dynamic system for retrieving CPU and GPU release dates from multiple sources
with caching, fallback logic, and future-proofing capabilities.
"""

import json
import os
import time
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HardwareInfo:
    """Hardware information with release date"""
    name: str
    release_date: str  # Hardware release date (not collection date)
    source: str  # 'api', 'cache', 'fallback'
    confidence: float  # 0.0 to 1.0
    last_updated: str

class HardwareReleaseDateManager:
    """Manages hardware release date lookups with multiple data sources"""
    
    def __init__(self, cache_file: str = "hardware_cache.json", cache_days: int = 30):
        self.cache_file = cache_file
        self.cache_days = cache_days
        self.cache: Dict[str, HardwareInfo] = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HardwareInfoCollector/1.0'
        })
        
        # Load existing cache
        self._load_cache()
        
        # API endpoints (free/public APIs)
        self.api_endpoints = {
            'gpu_info': 'https://raw.githubusercontent.com/voidful/gpu-info-api/main/data/gpu-info.json',
            'cpu_benchmarks': 'https://www.cpubenchmark.net/api/data',  # May require API key
            'techpowerup_gpu': 'https://www.techpowerup.com/gpu-specs/',  # Scraping fallback
        }
        
        # Fallback hardcoded data (minimal, most common hardware)
        self.fallback_data = self._get_minimal_fallback_data()
    
    def _load_cache(self):
        """Load hardware cache from file"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                for key, data in cache_data.items():
                    self.cache[key] = HardwareInfo(
                        name=data['name'],
                        release_date=data['release_date'],
                        source=data['source'],
                        confidence=data['confidence'],
                        last_updated=data['last_updated']
                    )
                logger.info(f"Loaded {len(self.cache)} hardware entries from cache")
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            self.cache = {}
    
    def _save_cache(self):
        """Save hardware cache to file"""
        try:
            cache_data = {}
            for key, info in self.cache.items():
                cache_data[key] = {
                    'name': info.name,
                    'release_date': info.release_date,
                    'source': info.source,
                    'confidence': info.confidence,
                    'last_updated': info.last_updated
                }
            
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Saved {len(self.cache)} hardware entries to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _is_cache_valid(self, info: HardwareInfo) -> bool:
        """Check if cached data is still valid"""
        try:
            last_updated = datetime.fromisoformat(info.last_updated)
            return datetime.now() - last_updated < timedelta(days=self.cache_days)
        except:
            return False
    
    def _get_minimal_fallback_data(self) -> Dict[str, str]:
        """Minimal fallback data for most common hardware"""
        return {
            # Intel Core series (approximate)
            'core i9-13': '2022-10-20T00:00:00',
            'core i7-13': '2022-10-20T00:00:00', 
            'core i5-13': '2022-10-20T00:00:00',
            'core i9-12': '2021-11-04T00:00:00',
            'core i7-12': '2021-11-04T00:00:00',
            'core i5-12': '2021-11-04T00:00:00',
            'core i9-11': '2021-03-30T00:00:00',
            'core i7-11': '2021-03-30T00:00:00',
            'core i5-11': '2021-03-30T00:00:00',
            
            # AMD Ryzen series (approximate)
            'ryzen 9 7': '2022-09-27T00:00:00',
            'ryzen 7 7': '2022-09-27T00:00:00',
            'ryzen 5 7': '2022-09-27T00:00:00',
            'ryzen 9 5': '2020-11-05T00:00:00',
            'ryzen 7 5': '2020-11-05T00:00:00',
            'ryzen 5 5': '2020-11-05T00:00:00',
            
            # NVIDIA RTX series (approximate)
            'rtx 40': '2022-10-12T00:00:00',
            'rtx 30': '2020-09-17T00:00:00',
            'rtx 20': '2018-09-20T00:00:00',
            'gtx 16': '2019-04-23T00:00:00',
            'gtx 10': '2016-05-27T00:00:00',
            
            # AMD Radeon series (approximate)
            'radeon rx 6': '2020-11-18T00:00:00',
            'radeon rx 5': '2017-04-18T00:00:00',
            
            # Intel Graphics (approximate)
            'intel uhd graphics': '2017-01-03T00:00:00',
            'intel hd graphics': '2015-01-05T00:00:00',
            'intel iris xe': '2020-09-02T00:00:00',
            'intel arc': '2022-10-12T00:00:00',
        }
    
    def _clean_hardware_name(self, name: str) -> str:
        """Clean hardware name for better matching"""
        import re
        
        # Remove trademark symbols and parentheses
        cleaned = re.sub(r'[®™]', '', name.lower())
        cleaned = re.sub(r'\([^)]*\)', '', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _fetch_gpu_info_from_api(self, gpu_name: str) -> Optional[HardwareInfo]:
        """Fetch GPU info from external API"""
        try:
            response = self.session.get(self.api_endpoints['gpu_info'], timeout=10)
            response.raise_for_status()
            
            gpu_data = response.json()
            
            # Search for matching GPU
            for gpu in gpu_data:
                if gpu_name.lower() in gpu.get('name', '').lower():
                    return HardwareInfo(
                        name=gpu_name,
                        release_date=gpu.get('release_date', 'Unknown'),
                        source='api',
                        confidence=0.9,
                        last_updated=datetime.now().isoformat()
                    )
                    
        except Exception as e:
            logger.warning(f"Failed to fetch GPU info from API: {e}")
        
        return None
    
    def _fetch_cpu_info_from_api(self, cpu_name: str) -> Optional[HardwareInfo]:
        """Fetch CPU info from external API (placeholder for future implementation)"""
        # This would require a CPU-specific API
        # For now, return None to use fallback
        return None
    
    def _search_fallback_data(self, hardware_name: str) -> Optional[HardwareInfo]:
        """Search fallback data for hardware info"""
        cleaned_name = self._clean_hardware_name(hardware_name)
        
        # Try exact matches first
        for pattern, date in self.fallback_data.items():
            if pattern in cleaned_name:
                return HardwareInfo(
                    name=hardware_name,
                    release_date=date,
                    source='fallback',
                    confidence=0.6,  # Lower confidence for fallback
                    last_updated=datetime.now().isoformat()
                )
        
        return None
    
    def get_release_date(self, hardware_name: str, hardware_type: str = 'auto') -> str:
        """
        Get release date for hardware with multiple fallback strategies
        
        Args:
            hardware_name: Name of the hardware
            hardware_type: 'cpu', 'gpu', or 'auto' (auto-detect)
            
        Returns:
            Release date string or 'Unknown'
        """
        if not hardware_name or hardware_name.lower() == "unknown":
            return "Unknown"
        
        # Clean the hardware name for cache key
        cache_key = self._clean_hardware_name(hardware_name)
        
        # Check cache first
        if cache_key in self.cache:
            cached_info = self.cache[cache_key]
            if self._is_cache_valid(cached_info):
                logger.debug(f"Using cached data for {hardware_name}")
                return cached_info.release_date
            else:
                # Remove expired cache entry
                del self.cache[cache_key]
        
        # Try to determine hardware type if auto
        if hardware_type == 'auto':
            hardware_type = self._detect_hardware_type(hardware_name)
        
        # Try API lookup based on hardware type
        api_info = None
        if hardware_type == 'gpu':
            api_info = self._fetch_gpu_info_from_api(hardware_name)
        elif hardware_type == 'cpu':
            api_info = self._fetch_cpu_info_from_api(hardware_name)
        
        # If API lookup failed, try fallback data
        if api_info is None:
            api_info = self._search_fallback_data(hardware_name)
        
        # Use the best available info
        if api_info:
            # Cache the result
            self.cache[cache_key] = api_info
            self._save_cache()
            
            logger.info(f"Found release date for {hardware_name}: {api_info.release_date} (source: {api_info.source})")
            return api_info.release_date
        else:
            # Cache unknown result to avoid repeated lookups
            unknown_info = HardwareInfo(
                name=hardware_name,
                release_date='Unknown',
                source='none',
                confidence=0.0,
                last_updated=datetime.now().isoformat()
            )
            self.cache[cache_key] = unknown_info
            self._save_cache()
            
            logger.warning(f"No release date found for {hardware_name}")
            return "Unknown"
    
    def _detect_hardware_type(self, hardware_name: str) -> str:
        """Auto-detect hardware type from name"""
        name_lower = hardware_name.lower()
        
        # GPU indicators
        gpu_indicators = ['rtx', 'gtx', 'quadro', 'radeon', 'rx', 'graphics', 'gpu', 'video']
        if any(indicator in name_lower for indicator in gpu_indicators):
            return 'gpu'
        
        # CPU indicators
        cpu_indicators = ['core i', 'ryzen', 'pentium', 'celeron', 'xeon', 'cpu', 'processor']
        if any(indicator in name_lower for indicator in cpu_indicators):
            return 'cpu'
        
        # Default to unknown
        return 'unknown'
    
    def update_cache_from_external_source(self, source_url: str) -> bool:
        """
        Update cache from external data source
        
        Args:
            source_url: URL to fetch data from
            
        Returns:
            True if update was successful
        """
        try:
            response = self.session.get(source_url, timeout=30)
            response.raise_for_status()
            
            # This would parse the external data and update cache
            # Implementation depends on the specific data source format
            
            logger.info(f"Successfully updated cache from {source_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update cache from {source_url}: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_entries = len(self.cache)
        valid_entries = sum(1 for info in self.cache.values() if self._is_cache_valid(info))
        
        sources = {}
        for info in self.cache.values():
            sources[info.source] = sources.get(info.source, 0) + 1
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': total_entries - valid_entries,
            'sources': sources,
            'cache_file': self.cache_file,
            'cache_days': self.cache_days
        }

# Global instance for easy access
_hardware_manager = None

def get_hardware_manager() -> HardwareReleaseDateManager:
    """Get global hardware manager instance"""
    global _hardware_manager
    if _hardware_manager is None:
        _hardware_manager = HardwareReleaseDateManager()
    return _hardware_manager

def get_release_date(hardware_name: str, hardware_type: str = 'auto') -> str:
    """
    Convenience function to get hardware release date
    
    Args:
        hardware_name: Name of the hardware
        hardware_type: 'cpu', 'gpu', or 'auto'
        
    Returns:
        Release date string or 'Unknown'
    """
    manager = get_hardware_manager()
    return manager.get_release_date(hardware_name, hardware_type)

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    manager = get_hardware_manager()
    return manager.get_cache_stats()

# Test function
if __name__ == "__main__":
    # Test the system
    manager = HardwareReleaseDateManager()
    
    # Test cases
    test_hardware = [
        "Intel Core i7-13700",
        "NVIDIA GeForce RTX 4070",
        "AMD Ryzen 7 7700X",
        "Intel Arc Pro Graphics",
        "Unknown Hardware"
    ]
    
    print("Testing Hardware Release Date Manager:")
    print("=" * 50)
    
    for hardware in test_hardware:
        date = manager.get_release_date(hardware)
        print(f"{hardware}: {date}")
    
    print("\nCache Statistics:")
    print("=" * 50)
    stats = manager.get_cache_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
