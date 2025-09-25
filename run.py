# #!/usr/bin/env python3
# """
# Startup script for the Flask Background Worker Bot.
# This script provides different ways to run the application.
# """
# import os
# import sys
# import argparse
# from app import create_app
# from config import config


# def main():
#     """Main entry point for the application."""
#     parser = argparse.ArgumentParser(description='Flask Background Worker Bot')
#     parser.add_argument(
#         '--env',
#         choices=['development', 'production', 'testing'],
#         default='development',
#         help='Environment to run in (default: development)'
#     )
#     parser.add_argument(
#         '--port',
#         type=int,
#         default=5000,
#         help='Port to run on (default: 5000)'
#     )
#     parser.add_argument(
#         '--host',
#         default='0.0.0.0',
#         help='Host to bind to (default: 0.0.0.0)'
#     )
#     parser.add_argument(
#         '--worker-only',
#         action='store_true',
#         help='Run only the background worker without Flask server'
#     )

#     args = parser.parse_args()

#     # Set environment
#     os.environ['FLASK_ENV'] = args.env

#     if args.worker_only:
#         # Run only the background worker
#         print("Starting background worker only...")
#         from worker import BackgroundWorker
#         worker = BackgroundWorker()

#         try:
#             worker.start()
#             print("Background worker started. Press Ctrl+C to stop.")

#             # Keep the worker running
#             import signal
#             import time

#             def signal_handler(sig, frame):
#                 print("\nStopping background worker...")
#                 worker.stop()
#                 sys.exit(0)

#             signal.signal(signal.SIGINT, signal_handler)
#             signal.signal(signal.SIGTERM, signal_handler)

#             while True:
#                 time.sleep(1)

#         except KeyboardInterrupt:
#             print("\nShutting down...")
#             worker.stop()

#     else:
#         # Run the full Flask application with background worker
#         app = create_app()

#         print(f"Starting Flask Background Worker Bot")
#         print(f"Environment: {args.env}")
#         print(f"Host: {args.host}")
#         print(f"Port: {args.port}")
#         print(f"Debug: {args.env == 'development'}")

#         app.run(
#             host=args.host,
#             port=args.port,
#             debug=(args.env == 'development')
#         )


# if __name__ == '__main__':
#     main()
