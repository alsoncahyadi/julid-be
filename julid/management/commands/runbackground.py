from django.core.management.base import BaseCommand, CommandError
from julid.scraper import forever_run

class Command(BaseCommand):
    help = 'Forever running the scrapper'

    # def add_arguments(self, parser):
    #     pass
    #     # for passing arguments

    def handle(self, *args, **options):
        forever_run()
