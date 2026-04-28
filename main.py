"""
Lead Generation & Outreach Tool
Main CLI entry point
"""

import argparse
import logging
import sys
from config import Config
from database import Database
from collector import LeadCollector
from analyzer import WebsiteAnalyzer
from email_extractor import EmailExtractor
from mailer import Mailer
from scheduler import Scheduler
from utils import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    parser = argparse.ArgumentParser(
        description="Lead Generation & Outreach Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  collect      Search for leads via Google Maps Places API
  analyze      Analyze websites for NopCommerce or missing websites
  extract      Extract emails from lead websites
  send_emails  Send personalized outreach emails
  schedule     Start the automated scheduler
  stats        Show database statistics

Examples:
  python main.py collect --keyword "clothing stores" --location "London"
  python main.py analyze
  python main.py extract
  python main.py send_emails --dry-run
  python main.py stats
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # collect command
    collect_parser = subparsers.add_parser("collect", help="Collect leads from Google Maps")
    collect_parser.add_argument("--keyword", required=True, help="Business type (e.g. 'clothing stores')")
    collect_parser.add_argument("--location", required=True, help="Location (e.g. 'London')")
    collect_parser.add_argument("--max-results", type=int, default=20, help="Max results to fetch (default: 20)")

    # analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze websites for NopCommerce or detect missing websites")
    analyze_parser.add_argument("--limit", type=int, default=50, help="Max leads to analyze (default: 50)")

    # extract command
    extract_parser = subparsers.add_parser("extract", help="Extract emails from websites")
    extract_parser.add_argument("--limit", type=int, default=50, help="Max leads to process (default: 50)")

    # send_emails command
    send_parser = subparsers.add_parser("send_emails", help="Send outreach emails")
    send_parser.add_argument("--dry-run", action="store_true", help="Simulate sending without actually sending")
    send_parser.add_argument("--limit", type=int, default=10, help="Max emails to send in this run (default: 10)")

    # schedule command
    subparsers.add_parser("schedule", help="Start automated scheduler")

    # stats command
    subparsers.add_parser("stats", help="Show statistics")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    # Load config and init database
    try:
        config = Config()
        db = Database(config.db_path)
        db.initialize()
    except Exception as e:
        logger.error(f"Initialization error: {e}")
        sys.exit(1)

    # Route commands
    if args.command == "collect":
        collector = LeadCollector(config, db)
        count = collector.collect(keyword=args.keyword, location=args.location, max_results=args.max_results)
        print(f"\n✅ Collected {count} leads for '{args.keyword}' in '{args.location}'")

    elif args.command == "analyze":
        analyzer = WebsiteAnalyzer(config, db)
        results = analyzer.analyze_all(limit=args.limit)
        print(f"\n✅ Analysis complete: {results['nopcommerce']} NopCommerce sites, {results['no_website']} missing websites, {results['analyzed']} total analyzed")

    elif args.command == "extract":
        extractor = EmailExtractor(config, db)
        count = extractor.extract_all(limit=args.limit)
        print(f"\n✅ Email extraction complete: {count} emails found")

    elif args.command == "send_emails":
        mailer = Mailer(config, db)
        count = mailer.send_outreach(limit=args.limit, dry_run=args.dry_run)
        mode = "simulated" if args.dry_run else "sent"
        print(f"\n✅ {count} emails {mode}")

    elif args.command == "schedule":
        scheduler = Scheduler(config, db)
        print("🕐 Starting scheduler... (Ctrl+C to stop)")
        scheduler.start()

    elif args.command == "stats":
        stats = db.get_stats()
        print("\n📊 Database Statistics")
        print("=" * 40)
        for key, value in stats.items():
            print(f"  {key:<30} {value}")

if __name__ == "__main__":
    main()
