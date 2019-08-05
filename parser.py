import threading
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import common
from req import Req
from datetime import datetime
import gevent
from browser import Browser
import time


def check_captcha_google(driver):  # Проверяет не подсовывает ли google капчу
    try:
        driver.find_element_by_id("captcha-form")
    except common.exceptions.NoSuchElementException:
        return False
    else:
        return True


def check_captcha_yandex(driver):  # Проверяет не подсовывает ли yandex капчу
    print('зашлов в функцию проверки капчи яндекса')  # ----------------------------------------------------
    print(driver.title)
    if 'Ой!' in driver.title:
        print('отправляет True')  # ----------------------------------------------
        return True
    else:
        print('отправляет False')  # ----------------------------------------------
        return False


def ran_pages_google(req_i, driver, namber = 0, namber_page = 0):  # Проверка сраницы с ответами гугл
    print('порт {} зашли в функцию ran_pages_google, проверяем на капчу'.format(driver.use_proxy_port))  # -----------
    if check_captcha_google(driver):  # Проверяем не подсовывает ли google капчу
        print('порт {} попалась капча, возвращаем None, None'.format(driver.use_proxy_port))  # -------------
        return None, None
    page = driver.find_element(By.XPATH, "//*[@id='search']")  # page = driver.find_element_by_id("search")
    results = page.find_elements(By.XPATH, ".//div[@class='g']")
    print('порт {} получили список результатов длинной {}'.format(driver.use_proxy_port, len(results)))  # -------------
    for i, result in enumerate(results):
        try:  # xpath_str = "[contains(text(),'{}')]".format(cite_name)
            find_cite = result.find_element_by_xpath('.//cite')
        except common.exceptions.NoSuchElementException:
            continue
        if req_i.site_promoted in find_cite.text:
            print('порт {} найден продвигаемый сайт в поиске'.format(driver.use_proxy_port))  # -------------
            return namber + 1, find_cite.text
        else:
            namber += 1
    namber_page += 1
    if namber_page == 10:  # листает 10 страниц, если не находит, возврщает 101
        print('порт {} пролистали 10 страниц, сайта в поиске нет'.format(driver.use_proxy_port))  # -------------
        return 101, None
    driver.find_element_by_xpath(".//a[@aria-label='Page {0}'][text()='{0}']".format(namber_page + 1)).click()
    return ran_pages_google(req_i, driver, namber, namber_page)


def ran_pages_yandex(req_i, driver, namber = 0, namber_page = 0):  # Проверка сраницы с ответами яндекс
    print('порт {} зашли в функцию ran_pages_yandex, проверяем на капчу'.format(driver.use_proxy_port))  # -------------
    time.sleep(5)
    results = driver.find_elements(By.XPATH, ".//li[@class='serp-item' and @data-cid]")  # получаем список результатов
    print('порт {} получили список результатов длинной {}'.format(driver.use_proxy_port, len(results)))  # -------------
    if len(results) == 0 and check_captcha_yandex(driver):  # проверка на капчу
        print('порт {} попалась капча, возвращаем None, None'.format(driver.use_proxy_port))  # -------------

        return None, None
    if len(results) < 5:
        gevent.sleep(9999)

    for i, r in enumerate(results):
        try:
            r.find_element(By.XPATH, ".//div[contains(@class, 'label') and text()='реклама']")  # проверка рекламы
        except common.exceptions.NoSuchElementException:  # Значит не реклама, продолжаем
            find_cite = r.find_element(By.XPATH, ".//a")
            if req_i.site_promoted in find_cite.get_attribute("href"):
                print('порт {} найден продвигаемый сайт в поиске'.format(driver.use_proxy_port))  # -------------
                return namber + 1, find_cite.get_attribute("href")  # возвращаем номер и найденую ссылку
            else:
                namber += 1
        else:
            continue
    namber_page += 1
    if namber_page == 10:  # листает 10 страниц, если не находит, возврщает 101
        print('порт {} пролистали 10 страниц, сайта в поиске нет'.format(driver.use_proxy_port))  # -------------
        return 101, None
    try:
        aria_label = driver.find_element_by_xpath(".//div[@aria-label='Страницы']")  # aria-label="Страницы"
        aria_label.find_element_by_xpath(".//a[text()='{0}']".format(namber_page + 1)).click()
    except common.exceptions.NoSuchElementException:
        return None, None  # возвращаем None, пробуем с другого ip
    print('порт {} '.format(driver.use_proxy_port))  # -------------
    return ran_pages_yandex(req_i, driver, namber, namber_page)


def run_scraper(ports, reqs, requests_google, requests_yandex):
    print('запуск задачи с поротом {}  '.format(ports[0]))  # --------------------------

    def search_google(driver, use_req):  # Поиск в google
        try:
            driver.get('https://www.google.by')
            print('порт {} зашли на сайт гугл пробуем сдеать запрос'.format(driver.use_proxy_port))  # -------------
            page = driver.find_element(By.XPATH, ".//input[@title='Search' or @title='Поиск' or @title='Шукаць']")
            print('порт {} ищем элемент <поиск>'.format(driver.use_proxy_port))  # -------------
            page.send_keys(use_req.value_req)
            page.send_keys(Keys.RETURN)
            print('порт {} ввели запрос. переходим к функции ran_pages_google'.format(driver.use_proxy_port))  # -------------
            use_req.position_google, use_req.url_result_google = ran_pages_google(use_req, driver)
            print('порт {} сделали запрос в гугл. идем на страницу с результатами'.format(driver.use_proxy_port))  # -------------
        except common.exceptions.NoSuchElementException:
            print('порт {} исключение в блоке запроса гуглу'.format(driver.use_proxy_port))  # -------------
            use_req.position_google, use_req.url_result_google = None, None

    def search_yandex(driver, use_req):  # Поиск в яндексе
        look = threading.RLock()

        try:
            driver.get('https://yandex.by')
            look.acquire()
            print('порт {} пробуем задать запрос в яндекс'.format(driver.use_proxy_port))  # -------------
            page = driver.find_element(By.XPATH, ".//*[@id='text']")  # Поиск
            page.send_keys(use_req.value_req)
            page.send_keys(Keys.RETURN)
            look.release()
            use_req.position_yandex, use_req.url_result_yandex = ran_pages_yandex(use_req, driver)
            print('порт {} идем на странуцу с результатами запросов в яндексе'.format(driver.use_proxy_port))  # -------------
        except common.exceptions.NoSuchElementException:
            print('порт {} исключение в блоке запроса яндексу'.format(driver.use_proxy_port))  # -------------
            use_req.position_yandex, use_req.url_result_yandex = None, None


    look = threading.RLock()
    while True:
        look.acquire()
        browser = Browser(ports=ports)  # True , headless=False
        browser.implicitly_wait(8)
        look.release()
        print('порт {} зашел в цикл в оснойной цикл вайл строка 101'.format(ports[0]))  # -------------------------------------------------------------------
        while requests_google:  # цикл работает если не все запросы в гугл выполнены
            print('порт {} зашел в цикл работы с гугл стр 103 len(requests_google) = {}'.format(ports[0], len(requests_google))) # --
            look.acquire()
            use_req_for_google = reqs[requests_google.pop()]  # берет последний id запроса в списке requests_google
            look.release()
            print('порт {} используем запрос с id = {} стр 105 '.format(ports[0], use_req_for_google.id))  # -------------------------------------------------------------------
            search_google(browser, use_req_for_google)
            print('порт {} выполнена функция search_google стр 107'.format(ports[0]))  # -------------------------------------------------------------------
            flag_bad_proxy = True if use_req_for_google.position_google is None else False
            print('порт {} flag_bad_proxy = {} стр 109'.format(ports[0], flag_bad_proxy))  # -------------------------------------------------------------------
            if flag_bad_proxy:  # если попалась капча поднимется флаг, переходим к яндексу
                requests_google.append(use_req_for_google.id)  # возвращаем не обработаный запрос
                print('порт {} попалась капча, выходим из цикла для гугла и переходим к яндексу стр 111'.format(ports[0]))  # -------------------------------------------------------------------
                break
            else:  # если ответ получен, запишим результат и попробуем следующий запрос
                look.acquire()

                print('порт {} стр 121. получаем обьект Req'.format(ports[0]))  # --------------------------------------------
                req = reqs[use_req_for_google.id]
                print('порт {} стр 123. получили обьект Req, его id = {}, нужен был id = {}'.format(ports[0],req.id , use_req_for_google.id))  # --------------------------------------------
                try:
                    print('порт {} стр 125 сейчас будем соеденять обьекты Req'.format(ports[0]))  # --------------------------------------------
                    req.combine(use_req_for_google)  # обьеденияем экзмляр Req со своим клоном
                    print('порт {} стр 127 поробовали соединить'.format(ports[0]))  # --------------------------------------------
                except KeyError as err:
                    print('порт {} соединение обьекта Req не удалось стр 129'.format(ports[0]))  # --------------------------------------------
                    print(err)
                look.release()
        while requests_yandex:
            print('порт {} зашел в цикл работы с яндекс стр 132 len(requests_yandex) = {}'.format(ports[0], len(requests_yandex))) # -----
            look.acquire()
            use_req_for_yandex = reqs[requests_yandex.pop()]
            look.release()
            print('порт {} используем запрос с id = {} стр 134 '.format(ports[0], use_req_for_yandex.id))  # ---------------------------------------
            search_yandex(browser, use_req_for_yandex)
            print('порт {} выполнена функция search_yandex стр 136'.format(ports[0]))  # --------------------------------
            flag_bad_proxy = True if use_req_for_yandex.position_yandex is None else False
            print('порт {} flag_bad_proxy = {} стр 138'.format(ports[0], flag_bad_proxy))  # -----------------------------------------------------
            if flag_bad_proxy:  # если попалась капча поднимется флаг, меняем ip и чистим куки
                requests_yandex.append(use_req_for_yandex.id)  # возвращаем не обработаный запрос
                print('порт {} попалась капча, выходим из цикла. теперь нужно сменить ip и очистить куки стр 140'.format(ports[0]))  # ------------------------
                break
            else:  # если ответ получен, запишим результат и попробуем следующий запрос
                print('порт {} капча не попалась пробуем записать результат стр 143. пробуем удалить id из очереди requests_yandex. удаляемый id = {}'.format(ports[0], use_req_for_yandex.id))  # --------
                look.acquire()
                print('порт {} стр 150. получаем обьект Req'.format(ports[0]))  # ---------------------------------
                req = reqs[use_req_for_yandex.id]
                print('порт {} стр 152. получили обьект Req, его id = {}, нужен был id = {}'.format(ports[0], req.id, use_req_for_yandex.id))  # ------
                try:
                    req.combine(use_req_for_yandex)  # обьеденияем экзмляр Req со своим клоном
                    print('порт {} стр 155 поробовали соединить обьекты Req'.format(ports[0]))  # ------------------------
                except KeyError as err:
                    print('порт {} соединение обьекта Req не удалось стр 157'.format(ports[0]))  # --------
                    print(err)
                look.release()
        print('порт {} необходимо сменить ip и стереть куки'.format(ports[0]))  # --------
        browser.delete_all_cookies()  # чистим куки
        browser.quit()
        if not any(requests_google, requests_yandex):  # если все запросы выполнены, то выходим  and
            print('порт {} вышел из основного цикла, колличесто элементов в requests_google {}'.format(ports[0], len(requests_google)))  # --------
            break
        browser.restart_proxy()  # меняем ip
        print('порт {} смeнили ip'.format(ports[0]))  # --------
        print('порт {} стерли куки, пробуем предать управление другому таску'.format(ports[0]))  # --------
        print('порт {} завершаем основной цикл task'.format(ports[0]))  # --------

    return 'поток с поротоm {} закончил работу'.format(ports[0])


if __name__ == '__main__':
    read_file_name = 'list_requests'  # read_file_name = input('filename: ')
    if 'json' in (read_file_name):
        reqs = Req.read_json(read_file_name)
    else:
        reqs = Req.read_txt(read_file_name)
    requests_google = [req.id for req in reqs]  # список id не сделаных запросов гугл
    requests_google.reverse()  # переверням. теперь можно брать первые id с конца
    requests_yandex = requests_google.copy()  # список id не сделаный запросов в яндекс
    time_now = datetime.now(tz=None)
    print("time start {}:{}:{}".format(time_now.hour, time_now.minute, time_now.second))

    stream1 = threading.Thread(target=run_scraper, args=((9050, 9051), reqs, requests_google, requests_yandex))
    stream2 = threading.Thread(target=run_scraper, args=((9060, 9061), reqs, requests_google, requests_yandex))
    stream3 = threading.Thread(target=run_scraper, args=((9062, 9063), reqs, requests_google, requests_yandex))
    stream4 = threading.Thread(target=run_scraper, args=((9065, 9066), reqs, requests_google, requests_yandex))
    stream1.start()
    stream2.start()
    stream3.start()
    stream4.start()
    stream1.join()
    stream2.join()
    stream3.join()
    stream4.join()

    Req.create_json(reqs)
    time_now = datetime.now(tz=None)
    print("time finish {}:{}:{}".format(time_now.hour, time_now.minute, time_now.second))
