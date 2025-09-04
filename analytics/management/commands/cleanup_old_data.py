from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone
from analytics.models import PlayHistory

class Command(BaseCommand):
    help = 'Deletes analytics data older than a specified retention period.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--retention-days',
            type=int,
            default=365,
            help='The number of days to retain PlayHistory data. Defaults to 365.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Don't actually delete records, just show how many would be deleted.",
        )

    def handle(self, *args, **options):
        retention_days = options['retention_days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timedelta(days=retention_days)

        self.stdout.write(f'Finding PlayHistory records older than {cutoff_date}...')

        old_records = PlayHistory.objects.filter(created_at__lt=cutoff_date)
        count = old_records.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS('No old records to delete.'))
            return

        self.stdout.write(f'Found {count} records to delete.')

        if dry_run:
            self.stdout.write(self.style.WARNING('This is a dry run. No records will be deleted.'))
        else:
            self.stdout.write('Deleting records...')
            # In a real-world scenario with a large table, you would delete in batches
            # to avoid locking the table for a long time.
            # For example:
            # while old_records.exists():
            #     batch = old_records.values_list('pk', flat=True)[:1000]
            #     PlayHistory.objects.filter(pk__in=list(batch))._raw_delete(old_records.db)
            #     self.stdout.write('Deleted a batch of 1000 records.')

            deleted_count, _ = old_records.delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} records.'))
