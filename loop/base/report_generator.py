import datetime
import pandas as pd
import time
from utils import change_timezone, timezone_aware
from django.db import connection as db_connection
from django.db.utils import OperationalError
from asgiref.sync import sync_to_async

from .models import StoreZone, StoreStatus, MenuHours


class ReportGenerator():
    """
    Handling Report Generation in an async way
    
    Methods:
    ---------
        last_hour
        last_day
        last_week
        generate_week
        status_count
        uptime_downtime
        helper
    """

    def last_hour(
            self,
            qs,
            current_timestamp,
            store_status_qs
    ):
        """
        Method to calculate uptime and downtime for last hour
        """
        last_hour_start_time = current_timestamp - \
            datetime.timedelta(hours=1)
        if current_timestamp < last_hour_start_time:
            current_timestamp = current_timestamp + \
                datetime.timedelta(days=1)
        uptime_last_hour, downtime_last_hour = \
            self.helper(
                qs, store_status_qs,
                last_hour_start_time, current_timestamp
            )
        return uptime_last_hour, downtime_last_hour

    def last_day(self, qs, store_hours_qs, store_status_qs, current_timestamp):
        """
        Method to calulate uptime and downtime for last day
        """
        current_weekday = current_timestamp.weekday()
        # extract store timmings for last day
        hours_filter_qs = store_hours_qs.filter(
            store_id=qs,
            dayOfWeek=current_weekday-1
        )
        last_day_start_time = current_timestamp - \
            datetime.timedelta(days=1)

        if qs.open24x7:
            uptime_24_hours, downtime_24_hours = \
                self.helper(
                    qs, store_status_qs,
                    last_day_start_time, current_timestamp
                )
        elif hours_filter_qs:
            # store was active on previous day within a 24 hours window
            if current_timestamp.time() < \
                    hours_filter_qs.first().start_time.time():
                start_time = datetime.datetime.combine(
                    last_day_start_time.date(),
                    hours_filter_qs.first().start_time.time()
                )
                end_time = datetime.datetime.combine(
                    last_day_start_time.date(),
                    hours_filter_qs.first().end_time.time()
                )
                start_time = timezone_aware(start_time, qs.timezone)
                end_time = timezone_aware(end_time, qs.timezone)
                # with a 24 hours window day got changed 
                # i.e. store was active in night window
                if end_time.time() < start_time.time():
                    end_time = end_time + datetime.timedelta(days=1)
                uptime_24_hours, downtime_24_hours = \
                    self.helper(
                        qs, store_status_qs, start_time, end_time
                    )
            # store was active partially for current day as 
            # well was active on last day within a 24 hours window
            elif (
                current_timestamp.time() >
                hours_filter_qs.first().start_time.time()
            ) and (
                current_timestamp.time() <
                hours_filter_qs.first().end_time.time()
            ):
                start_time_a = last_day_start_time
                end_time_a = datetime.datetime.combine(
                    last_day_start_time.date(),
                    hours_filter_qs.first().end_time.time()
                )
                start_time_b = datetime.datetime.combine(
                    current_timestamp.date(),
                    hours_filter_qs.first().start_time.time()
                )
                end_time_b = current_timestamp
                end_time_a = timezone_aware(end_time_a, qs.timezone)
                start_time_b = timezone_aware(start_time_b, qs.timezone)
                if end_time_a.time() < start_time_a.time():
                    end_time_a = end_time_a + \
                        datetime.timedelta(days=1)
                if end_time_b.time() < start_time_b.time():
                    end_time_b = end_time_b + \
                        datetime.timedelta(days=1)
                active_status_a, inactive_status_a = self.status_count(
                    qs, store_status_qs, start_time_a, end_time_a
                )
                active_status_b, inactive_status_b = self.status_count(
                    qs, store_status_qs, start_time_b, end_time_b
                )
                active_time = (
                    (end_time_b-start_time_b)+(end_time_a-start_time_a)
                )
                active_status = active_status_a + active_status_b
                inactive_status = inactive_status_a + inactive_status_b
                uptime_24_hours, downtime_24_hours = self.uptime_downtime(
                    active_status, inactive_status, active_time
                )
            # store has active hours on current day  within a 24 hours window
            else:
                start_time = datetime.datetime.combine(
                    current_timestamp.date(),
                    hours_filter_qs.first().start_time.time()
                )
                end_time = datetime.datetime.combine(
                    current_timestamp.date(),
                    hours_filter_qs.first().end_time.time()
                )
                start_time = timezone_aware(start_time, qs.timezone)
                end_time = timezone_aware(end_time, qs.timezone)
                # with a 24 hours window day got changed 
                # i.e. store was active in night window
                if end_time.time() < start_time.time():
                    end_time = end_time + datetime.timedelta(days=1)
                uptime_24_hours, downtime_24_hours = \
                    self.helper(
                        qs, store_status_qs, start_time, end_time
                    )
        else:
            uptime_24_hours = 0
            downtime_24_hours = 0
        return uptime_24_hours, downtime_24_hours

    def last_week(self, qs, store_status_qs, store_hours_qs, current_timestamp):
        """
        Method to calulate uptime and downtime for last week
        """
        current_weekday = current_timestamp.weekday()
        # calculating date for last sunday (end of week)
        last_week_end_date = current_timestamp - \
            datetime.timedelta(days=current_weekday+1)
        # calculating date for last monday (start of week)
        last_week_start_date = last_week_end_date - datetime.timedelta(days=6)
        if qs.open24x7:
            uptime_last_week, downtime_last_week = \
                self.helper(
                    qs, store_status_qs,
                    last_week_start_date, last_week_end_date
                )
        else:
            # get list of store opening days
            working_days_filter_qs = store_hours_qs.filter(
                store_id=qs
            )
            active_time, active_status, inactive_status = \
                datetime.timedelta(seconds=0), 0, 0
            for each_day in working_days_filter_qs:
                weekday_timestamp = last_week_start_date + \
                    datetime.timedelta(days=each_day.dayOfWeek)
                start_time = datetime.datetime.combine(
                    weekday_timestamp.date(),
                    each_day.start_time.time()
                )
                end_time = datetime.datetime.combine(
                    weekday_timestamp.date(),
                    each_day.end_time.time()
                )
                if each_day.end_time.time() < each_day.start_time.time():
                    end_time = end_time + datetime.timedelta(days=1)
                start_time = timezone_aware(start_time, qs.timezone)
                end_time = timezone_aware(end_time, qs.timezone)
                each_active_status, each_inactive_status = \
                    self.status_count(
                        qs, store_status_qs, start_time, end_time
                    )
                each_active_time = end_time - start_time
                active_status += each_active_status
                inactive_status += each_inactive_status
                active_time += each_active_time
            uptime_last_week, downtime_last_week = self.uptime_downtime(
                active_status, inactive_status, active_time
            )
        return uptime_last_week, downtime_last_week

    def generate_report(self, report_obj):
        """
        Threaded method to handle report generation
        """
        schema = [
            'store_id', 'uptime_last_hour(in minutes)',
            'uptime_last_day(in hours)', 'update_last_week(in hours)',
            'downtime_last_hour(in minutes)', 'downtime_last_day(in hours)',
            'downtime_last_week(in hours)'
        ]
        store_zone_qs = StoreZone.objects.all()
        store_status_qs = StoreStatus.objects.all()
        store_hours_qs = MenuHours.objects.all()
        current_timestamp = store_status_qs.order_by('-timestamp')\
            .first().timestamp
        report_stats = []

        total_stores, i = store_zone_qs.count(), 0
        for qs in store_zone_qs:
            i += 1
            # changing the current timestamp
            # from utc to stores timezone
            each_store_stats = [str(qs.store_id)]
            current_timestamp = change_timezone(
                current_timestamp,
                desired_timezone=qs.timezone
            )

            # for last hour
            uptime_last_hour, downtime_last_hour = self.last_hour(
                qs, current_timestamp, store_status_qs
            )

            # for last day (24 hours)
            uptime_24_hours, downtime_24_hours = self.last_day(
                qs, store_hours_qs, store_status_qs, current_timestamp
            )

            # for last week
            uptime_last_week, downtime_last_week = self.last_week(
                qs, store_status_qs, store_hours_qs, current_timestamp
            )
            if i % 1000 == 0:
                print(f"{i} of {total_stores} completed")

            each_store_stats.append(uptime_last_hour)
            each_store_stats.append(uptime_24_hours)
            each_store_stats.append(uptime_last_week)
            each_store_stats.append(downtime_last_hour)
            each_store_stats.append(downtime_24_hours)
            each_store_stats.append(downtime_last_week)
            report_stats.append(each_store_stats)
        file_path = f"report_{time.time()}.csv"
        df = pd.DataFrame(report_stats, columns=schema)
        df.to_csv(f"media/{file_path}", index=False)
        report_obj.path = file_path
        report_obj.status = "complete"
        report_obj.save()

        print("Report Generation Successful")

    def status_count(self, qs, store_status_qs, start_time, end_time):
        """
        To calculate a stores active probability
        b/w a specific time frame
        """
        status_filter_qs_24 = store_status_qs.filter(
            store_id=qs,
            timestamp__lte=end_time,
            timestamp__gte=start_time
        )
        active_status = status_filter_qs_24.filter(
            status="active").count()
        inactive_status = status_filter_qs_24.filter(
            status="inactive").count()
        return active_status, inactive_status

    def uptime_downtime(self, active_status, inactive_status, active_time):
        """
        Calculate uptime and downtime for a specific time period
        """
        try:
            active_percent = active_status/(
                active_status+inactive_status
            )
            uptime = active_time.total_seconds()*active_percent/60
            downtime = active_time.total_seconds()*(1-active_percent)/60
        except ZeroDivisionError:
            uptime = 0
            downtime = 0
        return uptime, downtime

    def helper(self, qs, store_status_qs, start_time, end_time):
        """
        Common helper function to calulate uptime and downtime
        """
        active_status, inactive_status = self.status_count(
            qs, store_status_qs, start_time, end_time
        )
        active_time = end_time - start_time
        uptime, downtime = self.uptime_downtime(
            active_status, inactive_status, active_time
        )

        return uptime, downtime
