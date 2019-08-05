"""
описывает класс Поисковый запрос
"""
import json
from datetime import datetime


class Req():
    namber = 0  # id запроса

    def __init__(self, **kwargs):
        self.id = Req.namber  # id запроса
        self.value_req = kwargs['value_req'] if 'value_req' in kwargs else None  # Значение запросов
        self.url_promoted = kwargs['url_promoted'] if 'url_promoted' in kwargs else None  # продвигаемая страница
        self.url_result_google = kwargs['url_result_google'] if 'url_result_google' in kwargs else None  # URL ответа
        self.url_result_yandex = kwargs['url_result_yandex'] if 'url_result_yandex' in kwargs else None  # URL ответа
        self.position_google = kwargs['position_google'] if 'position_google' in kwargs else None  # позиция в google
        self.position_yandex = kwargs['position_yandex'] if 'position_yandex' in kwargs else None  # позиция в yandex
        self.site_promoted = kwargs['site_promoted'] if 'site_promoted' in kwargs else None  # продвигаемый сайт
        self.google_captcha = False
        self.yandex_captcha = False
        Req.namber += 1

    def get_atr(self):
        req_dict = dict()
        req_dict[self.id] = {'site_promoted': self.site_promoted,
                             'value_req': self.value_req,
                             'url_promoted': self.url_promoted,
                             'url_result_google': self.url_result_google,
                             'url_result_yandex': self.url_result_yandex,
                             'position_google': self.position_google,
                             'position_yandex': self.position_yandex}
        return req_dict

    @classmethod
    def read_txt(cls, txt_name):  # читает текстовый файл и возвращает список обьектов req
        with open(txt_name, 'r', encoding='utf8') as read_file:
            read_file = read_file.read().split('\n')
        read_file.pop()
        oct_url_promoted, site, flag_type, reqs = '',  '', False, []
        for i in range(len(read_file)):
            if i == 0:
                site = read_file[i]
            elif read_file[i] == '':
                oct_url_promoted = read_file[i + 1] if read_file[i + 1] != '#' else None
                flag_type = True
            elif flag_type:
                flag_type = False
            else:
                reqs.append(Req(value_req=read_file[i], site_promoted=site, url_promoted=oct_url_promoted))
        return reqs

    @classmethod
    def read_json(cls, file_name):  # читает json и получает список обьектов Req
        with open(file_name, 'r', encoding='utf8') as file_json:
            dicts = json.loads(file_json.read())
        list_reqs = []
        for d in dicts:
            id = tuple(d.keys())[0]
            parameters = d[id]
            list_reqs.append(Req(id=id,
                                 site_promoted=parameters.get('site_promoted'),
                                 value_req=parameters.get('value_req'),
                                 url_promoted=parameters.get('url_promoted'),
                                 url_result_google=parameters.get('url_result_google'),
                                 url_result_yandex=parameters.get('url_result_yandex'),
                                 position_google=parameters.get('position_google'),
                                 position_yandex=parameters.get('position_yandex')))
        return list_reqs

    @classmethod
    def create_json(cls, list_class_reqs):  # принимает список обьектов req и записывает их в json
        time_now = datetime.now(tz=None)
        file_name = "positions_{}_{}_{}_{}.json".format(time_now.day, time_now.month, time_now.hour, time_now.minute)
        list_reqs = [rq.get_atr() for rq in list_class_reqs]
        with open(file_name, "w", encoding='utf8') as write_file:
            json.dump(list_reqs, write_file, ensure_ascii = False)


    def combine(self, another):  # обьеденяет экземпляр запроса с его клоном
        if self.id != another.id:
            raise KeyError('id экземпляров не совпадают!')
        else:
            if self.position_google is None:
                self.position_google = another.position_google
                self.url_result_google = another.url_result_google
            if self.position_yandex is None:
                self.position_yandex = another.position_yandex
                self.url_result_yandex = another.url_result_yandex
