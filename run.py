#!/usr/bin/env python3
"""
Simple startup script for the Trending Intelligence System
"""
import os
import sys
from app import create_app


def main():
    """Start the application with the new worker system"""
    try:
        app = create_app()
        print("🚀 Starting Trending Intelligence System...")
        print("📊 Enhanced LLM Pipeline Active")
        print("🔄 Background Worker: ENABLED")
        print("🌐 Flask API: http://localhost:5000")
        print("\n💡 Press Ctrl+C to stop")

        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False
        )
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
        sys.exit(0)


if __name__ == '__main__':
    main()
