# encoding=utf-8

import unittest
from SleepWakeExecutor import SleepingExecutor, LoginAgain
from datetime import datetime, timedelta
import time
from threading import Thread, active_count
import httpretty


try:
    # Python2
    from urllib import urlencode
except ImportError:
    # Python3
    from urllib.parse import urlencode

__author__ = 'mochenx'


class SleepingExecutorWithoutBooking(SleepingExecutor):
    def __init__(self, *args, **kwargs):
        super(SleepingExecutorWithoutBooking, self).__init__(*args, **kwargs)
        self.fire_cnt = 0
        self.fake_car_info = [{"YYRQ": "20141218", "XNSD": "812", "CNBH": "70032"},
                              {"YYRQ": "20141218", "XNSD": "812", "CNBH": "70040"},
                              {"YYRQ": "20141218", "XNSD": "812", "CNBH": "70041"}]

    def get_car_stat(self, date, time_period='Morning', do_retry=True):
        real_car_info = super(SleepingExecutorWithoutBooking, self).get_car_stat(date, time_period, do_retry)
        get_car_service_query = self.get_car_stat_qurey(date, self.booking_type, time_period)
        self.logger.debug(get_car_service_query, extra={'source': 'get_car_stat'})

        if do_retry:
            _, resp_body = self.session.open_n_read(url=get_car_service_query)
        else:
            _, resp_body = self.session.try_open_n_read(url=get_car_service_query)
        # Get car information form response
        car_info = self.parse_car_info_json(resp_body)
        self.logger.debug('Cars: {0} at time {1}'.format(str(car_info), datetime.now()),
                          extra={'source': 'get_car_stat'})

        if 'LoginOut' in car_info:
            raise LoginAgain()
        return self.fake_car_info if len(real_car_info) == 0 else real_car_info

    def book_car(self, car_info):
        book_car_query_args = {'yyrq': car_info[u'YYRQ'],
                               'xnsd': car_info[u'XNSD'],
                               'cnbh': car_info[u'CNBH'],
                               'imgCode': '',
                               'KMID': '1'}
        encoded_book_car_query_args = urlencode([(k, v) for k, v in book_car_query_args.items()])
        book_car_service_url = 'http://haijia.bjxueche.net/Han/ServiceBooking.asmx/BookingCar?'
        self.logger.debug(book_car_service_url+encoded_book_car_query_args, extra={'source': 'fake_book_car'})

        self.fire_cnt += 1
        if self.fire_cnt > 30:
            self.logger.debug('Fake True', extra={'source': 'fake_book_car'})
            return True
        self.logger.debug('Fake False', extra={'source': 'fake_book_car'})
        return False


class UTSleeping(unittest.TestCase):
    def setUp(self):
        today = datetime.now()
        self.the_day = today.replace(day=today.day + 7)
        self.executor = SleepingExecutor('1'*18, '0'*10, '1',
                                         book_date=self.the_day, time_period='Morning')

    # def test_login(self):
    #     success_cnt = 0
    #     for i in range(20):
    #         print('Round {0}:'.format(i))
    #         if self.executor.login(self.the_day.strftime('%Y%m%d')):
    #             print('Round {0} Login Successfully'.format(i))
    #             success_cnt += 1
    #         time.sleep(random.randrange(5, 30))
    #         print('Next Round')
    #     self.assertEqual(20, success_cnt)




    def test_sleep_n_book_on_date_without_booking_right_now(self):
        s_today = datetime.now().strftime('%Y%m%d')
        exector = SleepingExecutorWithoutBooking('210106198404304617', 'chen84430mo', '1',
                                                 book_date=datetime.strptime(s_today, '%Y%m%d'),
                                                 time_period='Morning')
        server_time = exector.get_server_time()
        self.next_n_minutes(exector, server_time, func_get_book_minute=lambda e: e + 3)
        exector.sleep_n_book_on_date()

    def test_sleep_n_book_on_date_without_booking_right_now_night(self):
        s_today = datetime.now().strftime('%Y%m%d')
        exector = SleepingExecutorWithoutBooking('130221198312055114', '1205', '2',
                                                 book_date=datetime.strptime('20141224', '%Y%m%d'),
                                                 time_period='Night')
        server_time = exector.get_server_time()
        self.next_n_minutes(exector, server_time, func_get_book_minute=lambda e: e + 3)
        exector.sleep_n_book_on_date()

    def test_sleep_n_book_on_date_without_booking_soon(self):
        s_today = datetime.now().strftime('%Y%m%d')
        exector = SleepingExecutorWithoutBooking('210106198404304617', 'chen84430mo', '1',
                                                 book_date=datetime.strptime(s_today, '%Y%m%d'),
                                                 time_period='Morning')
        server_time = exector.get_server_time()
        self.next_n_minutes(exector, server_time, func_get_book_minute=lambda e: e + 12)
        exector.sleep_n_book_on_date()

    def test_sleep_n_book_on_date_without_booking_tomorrow(self):
        today = datetime.now()
        s_tomorrow = today.replace(day=today.day+1).strftime('%Y%m%d')
        exector = SleepingExecutorWithoutBooking('210106198404304617', 'chen84430mo', '1',
                                                 book_date=datetime.strptime(s_tomorrow, '%Y%m%d'),
                                                 time_period='Morning')
        exector.sleep_n_book_on_date()

    def test_sleep_n_book_on_date_in_thread_right_now(self):
        s_today = datetime.now().strftime('%Y%m%d')
        # all_args = [(['210106198404304617', 'chen84430mo', '1'],
        #              {'book_date': datetime.strptime(s_today, '%Y%m%d'), 'time_period': 'Morning'}),
        #             (['230107198706211520', '0621', '1'],
        #              {'book_date': datetime.strptime(s_today, '%Y%m%d'), 'time_period': 'Morning'}),
        #             (['130221198312055114', '1205', '2'],
        #              {'book_date': datetime.strptime(s_today, '%Y%m%d'), 'time_period': 'Morning'}),
        # ]
        all_args = [(['130221198312055114', '1205', '1'],
                     {'book_date': datetime.strptime(s_today, '%Y%m%d'), 'time_period': 'Morning'}),
                    (['230107198706211520', '0621', '2'],
                     {'book_date': datetime.strptime(s_today, '%Y%m%d'), 'time_period': 'Morning'}),
                    ]

        def worker(*args, **kwargs):
            exector = SleepingExecutorWithoutBooking(*args, **kwargs)
            server_time = exector.get_server_time()
            self.next_n_minutes(exector, server_time, func_get_book_minute=lambda e: e + 3)
            exector.sleep_n_book_on_date()
            with open(args[0], 'w') as f:
                f.write('Thread {0} has done'.format(args[0]))


        working_threads = [Thread(target=worker, args=args, kwargs=kwargs) for args, kwargs in all_args]

        existed_threads = active_count()
        for a_thread in working_threads:
            print(a_thread.is_alive())
            rslt = a_thread.start()
            print(a_thread.is_alive())

        while active_count() > existed_threads:
            print('{0} threads are running'.format(active_count()))
            time.sleep(10)

    def test_get_date_from_http_header_tc0(self):
        http_resp = ['date:  Mon, 15 Dec 2014 17:08:20 GMT\n',
                     'content-type: text/plain; charset=utf-8\n',
                     'content-length: 12\n',
                     'server: Python/HTTPretty\n',
                     'status: 200\n',
                     'connection: close\n']
        http_time = self.executor.get_date_from_http_header(http_resp)
        self.assertEqual('Mon, 15 Dec 2014 17:08:20 GMT', http_time)

    def test_get_date_from_http_header_tc1(self):
        http_resp = ['Date:Mon, 15 Dec 2014 17:08:20 GMT  \r\n',
                     'content-type: text/plain; charset=utf-8\n',
                     'content-length: 12\n',
                     'server: Python/HTTPretty\n',
                     'status: 200\n',
                     'connection: close\n']
        http_time = self.executor.get_date_from_http_header(http_resp)
        self.assertEqual('Mon, 15 Dec 2014 17:08:20 GMT', http_time)

