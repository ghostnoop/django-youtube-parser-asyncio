import os
import sys

from django.core.management import BaseCommand

from parsing.management.commands.image_worker.image_uploader import upload_starter


class Command(BaseCommand):
    help = 'Imports list of relations to the system'

    def handle(self, *args, file=None, **options):
        upload_starter()
