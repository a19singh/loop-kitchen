from datetime import datetime
import pandas
from django.core.management.base import BaseCommand, CommandError

from base.models import (StoreStatus, MenuHours, StoreZone)
from utils import convert_timezone


class Command(BaseCommand):

    def handle(self, *args, **options):

        self.stdout.write(
            '-------------------- Start Db Dump --------------------\n'
        )

        zone_data = pandas.read_csv(
            'csv_data/bq-results-20230125-202210-1674678181880.csv',
            index_col=False
        )
        zone_data_total, i = zone_data.shape[0], 0
        try:
            for index in zone_data.index:
                i += 1
                StoreZone.objects.create(**{
                    'store_id': zone_data['store_id'][index],
                    'timezone': zone_data['timezone_str'][index],
                    'open24x7': False
                })
                if i % 1000 == 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Dumped {i} of {zone_data_total} in StoreZone'
                        )
                    )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Failed Db Dump: {i} of Store Zone'
                f'Reason: {e}'
            ))

        hours_data = pandas.read_csv(
            'csv_data/Menu hours.csv',
            index_col=False
        )
        hours_data_total, i = hours_data.shape[0], 0
        try:
            for index in hours_data.index:
                i += 1
                store_obj, _ = StoreZone.objects.get_or_create(
                    store_id=hours_data['store_id'][index]
                )
                obj = {
                    'store_id': store_obj,
                    'dayOfWeek': hours_data['day'][index],
                    'start_time': convert_timezone(
                        hours_data['start_time_local'][index],
                        time_zone=store_obj.timezone
                    ),
                    'end_time': convert_timezone(
                        hours_data['end_time_local'][0],
                        time_zone=store_obj.timezone
                    )
                }
                _ = MenuHours.objects.create(**obj)
                if i % 1000 == 0:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Dumped {i} of {hours_data_total} in MenuHours'
                        )
                    )
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Failed Db Dump: {i} of Menu Hours'
                f'\nReason: {e}'
            ))

        status_data = pandas.read_csv(
            'csv_data/store status.csv',
            index_col=False
        )
        status_data_total, i, skip = status_data.shape[0], 0, 0
        time_zone = "UTC"
        try:
            for index in status_data.index:
                format_ = "%Y-%m-%d %H:%M:%S.%f %Z"
                i += 1
                try:
                    try:
                        x = datetime.strptime(
                                status_data['timestamp_utc'][index],
                                format_
                        )
                    except Exception:
                        format_ = "%Y-%m-%d %H:%M:%S %Z"
                    store_obj, _ = StoreZone.objects.get_or_create(
                        store_id=status_data['store_id'][index]
                    )
                    data_obj = {
                        'store_id': store_obj,
                        'status': status_data['status'][index],
                        'timestamp': convert_timezone(
                            status_data['timestamp_utc'][index],
                            time_zone=time_zone,
                            input_time_format=format_
                        )
                    }
                    _ = StoreStatus.objects.create(**data_obj)
                    if i % 1000 == 0:
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'Dumped {i} of {status_data_total} '
                                f'in StoreStatus'
                            )
                        )
                except StoreZone.DoesNotExist:
                    skip += 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'Failed Db Dump: {i} of Store Status\n'
                f'Reason: {e}'
            ))

        self.stdout.write(
            '--------------------Finished Db Dump --------------------\n'
        )
        self.stdout.write(f"Skipped {skip}")


