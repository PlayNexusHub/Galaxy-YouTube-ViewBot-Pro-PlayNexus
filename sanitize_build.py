#!/usr/bin/env python3
"""
PlayNexus Build Sanitization Script
Scans and sanitizes codebase for API keys, secrets, and sensitive data
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

# File extensions to scan
SCAN_EXTENSIONS = ['.py', '.js', '.ts', '.json', '.env', '.yml', '.yaml', '.xml', '.cs', '.cpp', '.h', '.rs']

# Patterns to detect sensitive data
SENSITIVE_PATTERNS = [
    (r'api[_-]?key\s*[:=]\s*["\']([^"\']+)["\']', 'api_key', 'YOUR_API_KEY_HERE'),
    (r'secret\s*[:=]\s*["\']([^"\']+)["\']', 'secret', 'YOUR_SECRET_HERE'),
    (r'token\s*[:=]\s*["\']([^"\']+)["\']', 'token', 'YOUR_TOKEN_HERE'),
    (r'auth[_-]?token\s*[:=]\s*["\']([^"\']+)["\']', 'auth_token', 'YOUR_AUTH_TOKEN_HERE'),
    (r'password\s*[:=]\s*["\']([^"\']+)["\']', 'password', 'YOUR_PASSWORD_HERE'),
    (r'client[_-]?id\s*[:=]\s*["\']([^"\']+)["\']', 'client_id', 'YOUR_CLIENT_ID_HERE'),
    (r'private[_-]?key\s*[:=]\s*["\']([^"\']+)["\']', 'private_key', 'YOUR_PRIVATE_KEY_HERE'),
    (r'sk-[A-Za-z0-9]{20,}', 'openai_key', 'YOUR_OPENAI_KEY_HERE'),
    (r'ghp_[A-Za-z0-9]{36}', 'github_token', 'YOUR_GITHUB_TOKEN_HERE'),
    (r'AIza[0-9A-Za-z-_]{35}', 'google_api_key', 'YOUR_GOOGLE_API_KEY_HERE'),
]

# Files/directories to exclude
EXCLUDE_PATTERNS = [
    'node_modules',
    '.git',
    '__pycache__',
    '.venv',
    'venv',
    'build',
    'dist',
    'Final_Build',
    'sanitize_build.py',
    'version.json',
    'config_template.json',
    '.env.example',
]

class Sanitizer:
    def __init__(self, root_dir='.'):
        self.root_dir = Path(root_dir)
        self.report = {
            'timestamp': datetime.now().isoformat(),
            'files_scanned': 0,
            'files_modified': 0,
            'redactions': [],
            'errors': []
        }
        
    def should_scan_file(self, file_path):
        """Check if file should be scanned"""
        file_str = str(file_path)
        
        # Check extension
        if not any(file_str.endswith(ext) for ext in SCAN_EXTENSIONS):
            return False
            
        # Check exclude patterns
        for pattern in EXCLUDE_PATTERNS:
            if pattern in file_str:
                return False
                
        return True
    
    def sanitize_file(self, file_path):
        """Sanitize a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            original_content = content
            modified = False
            
            # Apply each pattern
            for pattern, key_type, replacement in SENSITIVE_PATTERNS:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    if len(match.group(1)) > 10:  # Only replace if it looks like a real key
                        # Check if it's already a placeholder
                        if 'YOUR_' in match.group(1) or 'PLACEHOLDER' in match.group(1):
                            continue
                            
                        content = content.replace(match.group(0), match.group(0).replace(match.group(1), replacement))
                        self.report['redactions'].append({
                            'file': str(file_path),
                            'type': key_type,
                            'line': content[:match.start()].count('\n') + 1,
                            'replaced': match.group(1)[:20] + '...' if len(match.group(1)) > 20 else match.group(1)
                        })
                        modified = True
            
            # Write back if modified
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.report['files_modified'] += 1
                return True
                
        except Exception as e:
            self.report['errors'].append({
                'file': str(file_path),
                'error': str(e)
            })
            
        return False
    
    def scan_directory(self):
        """Scan entire directory"""
        print("🔍 Starting sanitization scan...")
        print(f"📁 Root directory: {self.root_dir}")
        
        for root, dirs, files in os.walk(self.root_dir):
            # Remove excluded directories from dirs list
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in EXCLUDE_PATTERNS)]
            
            for file in files:
                file_path = Path(root) / file
                
                if self.should_scan_file(file_path):
                    self.report['files_scanned'] += 1
                    if self.sanitize_file(file_path):
                        print(f"✅ Sanitized: {file_path}")
        
        print(f"\n📊 Scan complete!")
        print(f"   Files scanned: {self.report['files_scanned']}")
        print(f"   Files modified: {self.report['files_modified']}")
        print(f"   Redactions: {len(self.report['redactions'])}")
        print(f"   Errors: {len(self.report['errors'])}")
    
    def save_report(self, output_file='build_logs/sanitization_report.txt'):
        """Save sanitization report"""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("PLAYNEXUS BUILD SANITIZATION REPORT\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Timestamp: {self.report['timestamp']}\n")
            f.write(f"Files Scanned: {self.report['files_scanned']}\n")
            f.write(f"Files Modified: {self.report['files_modified']}\n")
            f.write(f"Total Redactions: {len(self.report['redactions'])}\n")
            f.write(f"Errors: {len(self.report['errors'])}\n\n")
            
            if self.report['redactions']:
                f.write("REDACTIONS:\n")
                f.write("-" * 80 + "\n")
                for redaction in self.report['redactions']:
                    f.write(f"File: {redaction['file']}\n")
                    f.write(f"Type: {redaction['type']}\n")
                    f.write(f"Line: {redaction['line']}\n")
                    f.write(f"Replaced: {redaction['replaced']}\n")
                    f.write("-" * 80 + "\n")
            
            if self.report['errors']:
                f.write("\nERRORS:\n")
                f.write("-" * 80 + "\n")
                for error in self.report['errors']:
                    f.write(f"File: {error['file']}\n")
                    f.write(f"Error: {error['error']}\n")
                    f.write("-" * 80 + "\n")
        
        print(f"📄 Report saved to: {output_file}")

def main():
    """Main entry point"""
    sanitizer = Sanitizer()
    sanitizer.scan_directory()
    sanitizer.save_report()
    
    if sanitizer.report['files_modified'] > 0:
        print("\n⚠️  WARNING: Files were modified during sanitization!")
        print("   Review the sanitization report before building.")
    else:
        print("\n✅ No sensitive data found. Safe to build!")

if __name__ == '__main__':
    main()

