from django.core.management.base import BaseCommand
from datetime import datetime, timedelta
from analytics.tasks import aggregate_daily_user_analytics, aggregate_daily_content_analytics

class Command(BaseCommand):
    help = 'Recomputes analytics data for a given date range.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--from',
            dest='from_date',
            type=str,
            help='The start date for recomputation (YYYY-MM-DD).',
        )
        parser.add_argument(
            '--to',
            dest='to_date',
            type=str,
            help='The end date for recomputation (YYYY-MM-DD).',
        )
        parser.add_argument(
            '--days',
            type=int,
            help='Number of past days to recompute.',
        )

    def handle(self, *args, **options):
        from_date_str = options['from_date']
        to_date_str = options['to_date']
        days = options['days']

        if from_date_str and to_date_str:
            start_date = datetime.strptime(from_date_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(to_date_str, '%Y-%m-%d').date()
        elif days:
            end_date = datetime.now().date() - timedelta(days=1)
            start_date = end_date - timedelta(days=days - 1)
        else:
            self.stdout.write(self.style.ERROR('You must provide either --from and --to, or --days.'))
            return

        current_date = start_date
        while current_date <= end_date:
            self.stdout.write(f'Recomputing analytics for {current_date}...')
            aggregate_daily_user_analytics(day=current_date)
            aggregate_daily_content_analytics(day=current_date)
            self.stdout.write(self.style.SUCCESS(f'Successfully recomputed analytics for {current_date}.'))
            current_date += timedelta(days=1)
