#!/usr/bin/env python3
"""
Test script to demonstrate the credential fallback system
Run this from the 2-scraper directory to test credential loading
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from src.services.auth import AutoLogin

def test_credential_fallback():
    """Test the three-tier credential fallback system"""
    print("🧪 Testing Credential Fallback System")
    print("=" * 50)
    
    # Create AutoLogin instance
    auto_login = AutoLogin()
    
    print("1️⃣ Testing GitHub Secrets (Environment Variables)")
    print(f"   SCRAPER_EMAIL: {'✅ Set' if os.getenv('SCRAPER_EMAIL') else '❌ Not set'}")
    print(f"   SCRAPER_PASSWORD: {'✅ Set' if os.getenv('SCRAPER_PASSWORD') else '❌ Not set'}")
    
    print("\n2️⃣ Testing Local credentials.json")
    credentials_file = Path("credentials.json")
    print(f"   File exists: {'✅ Yes' if credentials_file.exists() else '❌ No'}")
    if credentials_file.exists():
        print(f"   File path: {credentials_file.absolute()}")
    
    print("\n3️⃣ Testing Credential Loading")
    print("   Attempting to load credentials...")
    
    try:
        success = auto_login.load_credentials()
        if success:
            print("   ✅ Credentials loaded successfully!")
            print(f"   📧 Email: {auto_login.credentials.get('email', 'N/A')}")
            print("   🔒 Password: [HIDDEN]")
        else:
            print("   ❌ No credentials available")
            print("   💡 The system will now show a GUI to create credentials.json")
    except Exception as e:
        print(f"   ❌ Error loading credentials: {e}")
    
    print("\n" + "=" * 50)
    print("🔐 Security Notes:")
    print("   • credentials.json is NOT tracked in git")
    print("   • File is stored locally in 2-scraper/ directory")
    print("   • GitHub secrets take priority over local file")
    print("   • GUI will appear if no credentials are found")

if __name__ == "__main__":
    test_credential_fallback()
