import threading
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium import common
from req import Req
from datetime import datetime
from browser import Browser


def get_ports(name_file='ports'):  # получает список поротов для proxy
    with open(name_file, 'r', encoding='utf-8') as file:
        ports = file.readlines()
    return list(map(lambda p: tuple(map(lambda i: int(i), (p.split()))), ports))


def check_captcha_google(driver):  # Проверяет не подсовывает ли google капчу
    try:
        driver.find_element_by_id("captcha-form")
    except common.exceptions.NoSuchElementException:
        return False
    else:
        return True


def choose_by(driver):  # выбирает by в настройках гугла
    driver.find_element_by_xpath('.//a[text()="Настройки"]').click()
    driver.find_element_by_xpath('.//a[text()="Настройки поиска"]').click()
    driver.find_element_by_xpath('.//div[@id="regiontBY"]/div/span').click()
    driver.find_element_by_xpath('.//div[text()="Сохранить"]').click()  # .send_keys (u '\ ue007')
    time.sleep(1)
    driver.switch_to_alert().accept()


def check_captcha_yandex(driver):  # Проверяет не подсовывает ли yandex капчу
    if 'Ой!' in driver.title:
        return True
    else:
        return False


def ran_pages_google(req_i, driver, namber = 0, namber_page = 0):  # Проверка сраницы с ответами гугл
    if check_captcha_google(driver):  # Проверяем не подсовывает ли google капчу
        return None, None
    page = driver.find_element(By.XPATH, "//*[@id='search']")  # page = driver.find_element_by_id("search")
    time.sleep(1)
    results = page.find_elements(By.XPATH, ".//div[@class='g']")
    if len(results) < 7:
        time.sleep(8)
        results = page.find_elements(By.XPATH, ".//div[@class='g']")
    for i, result in enumerate(results):
        links = result.find_elements(By.XPATH, ".//a")
        for link in links:
            if req_i.site_promoted in link.get_attribute('href'):
                return namber + 1, link.get_attribute('href')
        else:
            namber += 1
    namber_page += 1
    if namber_page == 10:  # листает 10 страниц, если не находит, возврщает 101
        return 101, None
    driver.find_element_by_xpath(".//a[@aria-label='Page {0}'][text()='{0}']".format(namber_page + 1)).click()
    return ran_pages_google(req_i, driver, namber, namber_page)


def ran_pages_yandex(req_i, driver, namber = 0, namber_page = 0):  # Проверка сраницы с ответами яндекс
    time.sleep(3)  # необходимо для полной прогрузки страницы, может найти не весь список результатов или капчу
    results = driver.find_elements(By.XPATH, ".//li[@class='serp-item' and @data-cid]")  # получаем список результатов
    if len(results) == 0 and check_captcha_yandex(driver):  # проверка на капчу
        return None, None
    elif len(results) < 7:  # страница могла все же не загрузиться полностью
        time.sleep(10)  # еще раз ищем список результатов
        results = driver.find_elements(By.XPATH, ".//li[@class='serp-item' and @data-cid]")
    for i, r in enumerate(results):
        try:
            r.find_element(By.XPATH, ".//div[contains(@class, 'label') and text()='реклама']")  # проверка рекламы
        except common.exceptions.NoSuchElementException:  # Значит не реклама, продолжаем
            find_cite = r.find_element(By.XPATH, ".//a").get_attribute('href')
            if req_i.site_promoted in find_cite:
                return namber + 1, find_cite  # возвращаем номер и найденую ссылку
            elif 'yandex' not in find_cite:
                namber += 1
        else:
            continue
    namber_page += 1
    if namber_page == 10:  # листает 10 страниц, если не находит, возврщает 101
        return 101, None
    try:
        aria_label = driver.find_element_by_xpath(".//div[@aria-label='Страницы']")  # aria-label="Страницы"
        aria_label.find_element_by_xpath(".//a[text()='{0}']".format(namber_page + 1)).click()
    except common.exceptions.NoSuchElementException:
        return None, None  # возвращаем None, пробуем с другого ip
    return ran_pages_yandex(req_i, driver, namber, namber_page)


def run_scraper(ports, reqs, requests_google, requests_yandex):

    def search_google(driver, use_req):  # Поиск в google
        try:
            driver.get('https://www.google.by')
            choose_by(browser)  # выбор в настройках гугл региона поиска
            if check_captcha_google(browser):  # проверка на капчу
                return None, None
            page = driver.find_element(By.XPATH, ".//input[@title='Search' or @title='Поиск' or @title='Шукаць']")
            page.send_keys(use_req.value_req)
            page.send_keys(Keys.RETURN)
            use_req.position_google, use_req.url_result_google = ran_pages_google(use_req, driver)
        except common.exceptions.NoSuchElementException:
            use_req.position_google, use_req.url_result_google = None, None

    def search_yandex(driver, use_req):  # Поиск в яндексе
        try:
            driver.get('https://yandex.by')
            page = driver.find_element(By.XPATH, ".//*[@id='text']")  # Поиск
            page.send_keys(use_req.value_req)
            page.send_keys(Keys.RETURN)
            use_req.position_yandex, use_req.url_result_yandex = ran_pages_yandex(use_req, driver)
        except common.exceptions.NoSuchElementException:
            use_req.position_yandex, use_req.url_result_yandex = None, None

    look = threading.RLock()
    while True:
        browser = Browser(ports=ports)  # headless=False -- если необходим графический интерфейс браузера
        browser.implicitly_wait(8)
        string = "\r Необработаных запросов yandex: {} google {} port {}" \
                 "".format(len(requests_yandex), len(requests_google), browser.use_proxy_port)
        print(string, end="")
        while requests_google:  # цикл работает если не все запросы в гугл выполнены
            look.acquire()  # ставим блокировку на requests_google
            use_req_for_google = reqs[requests_google.pop()]  # берет последний id запроса в списке requests_google
            look.release()  # снимаем блокировку requests_google
            search_google(browser, use_req_for_google)
            flag_bad_proxy = True if use_req_for_google.position_google is None else False
            if flag_bad_proxy:  # если попалась капча поднимется флаг, переходим к яндексу
                requests_google.append(use_req_for_google.id)  # возвращаем не обработаный запрос
                break
            else:  # если ответ получен, запишим результат и попробуем следующий запрос
                look.acquire()
                req = reqs[use_req_for_google.id]
                try:
                    req.combine(use_req_for_google)  # обьеденияем экзмляр Req со своим клоном
                except KeyError as err:
                    print(err)
                look.release()
        while requests_yandex:
            look.acquire()
            use_req_for_yandex = reqs[requests_yandex.pop()]
            look.release()
            search_yandex(browser, use_req_for_yandex)
            flag_bad_proxy = True if use_req_for_yandex.position_yandex is None else False
            if flag_bad_proxy:  # если попалась капча поднимется флаг, меняем ip и чистим куки
                requests_yandex.append(use_req_for_yandex.id)  # возвращаем не обработаный запрос
                break
            else:  # если ответ получен, запишим результат и попробуем следующий запрос
                look.acquire()
                req = reqs[use_req_for_yandex.id]
                try:
                    req.combine(use_req_for_yandex)  # обьеденияем экзмляр Req со своим клоном
                except KeyError as err:
                    print(err)
                look.release()
        browser.delete_all_cookies()  # чистим куки
        browser.quit()
        if not any((requests_google, requests_yandex)):  # если все запросы выполнены, то выходим
            break
        browser.restart_proxy()  # меняем ip
    return 'поток с поротоm {} закончил работу'.format(ports[0])


def pool_thread(ports, reqs, requests_google, requests_yandex):  # запускает парсинг в несколько потоков
    pool = []
    for port in ports:
        stream = threading.Thread(target=run_scraper, args=(port, reqs, requests_google, requests_yandex))
        pool.append(stream)
    for stream in pool:
        stream.start()
    for stream in pool:
        stream.join()


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
    ports = get_ports()  # получаем список портов
    pool_thread(ports, reqs, requests_google, requests_yandex)
    Req.create_json(reqs)
    time_now = datetime.now(tz=None)
    print("time finish {}:{}:{}".format(time_now.hour, time_now.minute, time_now.second))
    for r in reqs:
        print('id {} запрос "{}" позиция в гугле {} позиция в яндексе {}'.format(r.id, r.value_req, r.position_google, r.position_yandex))
