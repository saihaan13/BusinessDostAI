#!/usr/bin/env python3
"""
Business Dost AI – One-Command Setup Script

This script sets up the entire Business Dost AI app:
1. Creates the folder structure
2. Installs Node.js dependencies
3. Creates .env file from template
4. Prints next steps

Usage: python setup.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}  {text}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️ {text}{RESET}")

def print_info(text):
    print(f"{BLUE}ℹ️ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def check_nodejs():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            print_success(f"Node.js found: {version}")
            return True
        else:
            print_error("Node.js not found")
            return False
    except FileNotFoundError:
        print_error("Node.js not found")
        return False

def create_folders():
    """Create necessary folders"""
    folders = ['server', 'frontend', 'server/logs']
    for folder in folders:
        Path(folder).mkdir(parents=True, exist_ok=True)
    print_success("Folders created")

def create_env_file():
    """Create .env file from example"""
    env_example = Path('server/.env.example')
    env_file = Path('server/.env')

    if env_example.exists():
        shutil.copy(env_example, env_file)
        print_success("Created .env file from .env.example")
        print_info("Please edit server/.env and add your GROQ_API_KEY")
    else:
        # Create .env directly if .env.example doesn't exist
        env_content = """# Server
PORT=3001

# Security
JWT_SECRET=business-dost-ai-secret-key-change-this

# Database
SQLITE_PATH=./businessdost.db

# Groq AI (FREE – get from https://console.groq.com)
GROQ_API_KEY=gsk_your_key_here

# Frontend CORS
FRONTEND_ORIGIN=*
"""
        with open(env_file, 'w') as f:
            f.write(env_content)
        print_success("Created .env file")
        print_info("Please edit server/.env and add your GROQ_API_KEY")

def run_npm_install():
    """Run npm install in server folder"""
    print_info("Running npm install (this may take 1-2 minutes)...")
    try:
        result = subprocess.run(
            ['npm', 'install'],
            cwd='server',
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("npm install completed")
            return True
        else:
            print_error(f"npm install failed: {result.stderr}")
            return False
    except Exception as e:
        print_error(f"npm install failed: {str(e)}")
        return False

def create_readme():
    """Create README.md if it doesn't exist"""
    if not Path('README.md').exists():
        readme_content = """# Business Dost AI

**The AI Business Copilot for Indian SMEs**

Voice-first · WhatsApp-native · Zero training

## Quick Start

### 1. Install Node.js
Download from: https://nodejs.org

### 2. Run Setup
```bash
python setup.py
