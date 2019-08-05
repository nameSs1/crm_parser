from selenium import webdriver
from selenium import common
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from req import Req
from datetime import datetime
import subprocess


def create_new_proxy():  # Возвращает обьект webdriver с новым ip
    subprocess.getoutput('sudo service tor restart')
    opts = Options()
    opts.headless = True
    profile = webdriver.FirefoxProfile()  # profile_directory='/home/sergey/PycharmProjects/crm_parser/ProfileFireFox'
    profile.set_preference("network.proxy.type", 1)
    profile.set_preference("network.proxy.socks", '127.0.0.1')
    profile.set_preference("network.proxy.socks_port", 9050)
    profile.set_preference("network.proxy.socks_remote_dns", False)
    profile.set_preference("intl.accept_languages", "ru")
    profile.set_preference("network.cookie.cookieBehavior", 2)
    profile.update_preferences()
    driver = webdriver.Firefox(firefox_profile=profile, options=opts)  # options=opts
    driver.implicitly_wait(10)
    return driver


def check_captcha_google(driver):  # Проверяет не подсовывает ли google капчу
    try:
        driver.find_element_by_id("captcha-form")
    except common.exceptions.NoSuchElementException:
        return False
    else:
        return True


def check_captcha_yandex(driver):  # Проверяет не подсовывает ли yandex капчу
    if 'Ой!' in driver.title:
        return True
    else:
        return False


def ran_pages_google(req_i, driver, namber = 0, namber_page = 0):  # Проверка сраницы с ответами гугл
    if check_captcha_google(driver):  # Проверяем не подсовывает ли google капчу
        return None, None
    page = driver.find_element(By.XPATH, "//*[@id='search']")  # page = driver.find_element_by_id("search")
    results = page.find_elements(By.XPATH, ".//div[@class='g']")
    for i, result in enumerate(results):
        try:  # xpath_str = "[contains(text(),'{}')]".format(cite_name)
            find_cite = result.find_element_by_xpath('.//cite')
        except common.exceptions.NoSuchElementException:
            continue
        if req_i.site_promoted in find_cite.text:
            return namber + 1, find_cite.text
        else:
            namber += 1
    namber_page += 1
    if namber_page == 10:  # листает 10 страниц, если не находит, возврщает 101
        return 101, None
    driver.find_element_by_xpath(".//a[@aria-label='Page {0}'][text()='{0}']".format(namber_page + 1)).click()
    return ran_pages_google(req_i, driver, namber, namber_page)


def ran_pages_yandex(req_i, driver, namber = 0, namber_page = 0):  # Проверка сраницы с ответами яндекс
    if check_captcha_yandex(driver):  # проверка на капчу
        return None, None
    results = driver.find_elements(By.XPATH, ".//ul/li[@class='serp-item']")  # получаем список результатов
    driver.implicitly_wait(0)
    for i, r in enumerate(results):
        try:
            r.find_element(By.XPATH, ".//div[contains(@class, 'label') and text()='реклама']")  # проверка рекламы
        except common.exceptions.NoSuchElementException:  # Значит не реклама, продолжаем
            find_cite = r.find_element(By.XPATH, ".//a")
            if req_i.site_promoted in find_cite.get_attribute("href"):
                return namber + 1, find_cite.get_attribute("href")  # возвращаем номер и найденую ссылку
            else:
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
    driver.implicitly_wait(10)
    return ran_pages_yandex(req_i, driver, namber, namber_page)


def get_positions(reqs):  # Задаем поисковика полученый список запросов

    def search_google(driver, req_i):  # Поиск в google
        try:
            driver.get('https://www.google.by')
            page = driver.find_element(By.XPATH, ".//input[@title='Search' or @title='Поиск']")  # Шукаць
            page.send_keys(req_i.value_req)
            page.send_keys(Keys.RETURN)
            req_i.position_google, req_i.url_result_google = ran_pages_google(req_i, driver)
        except common.exceptions.NoSuchElementException:
            req_i.position_google, req_i.url_result_google = None, None

    def search_yandex(driver, req_i):  # Поиск в яндексе
        try:
            driver.get('https://yandex.by')
            page = driver.find_element(By.XPATH, ".//*[@id='text']")  # Поиск
            page.send_keys(req_i.value_req)
            page.send_keys(Keys.RETURN)
            req_i.position_yandex, req_i.url_result_yandex = ran_pages_yandex(req_i, driver)
        except common.exceptions.NoSuchElementException:
            req_i.position_yandex, req_i.url_result_yandex = None, None

    driver = create_new_proxy()
    for i, req_i in enumerate(start=1, iterable=reqs):  # Запросы в google
        search_google(driver, req_i)
        flag_bad_proxy = True if req_i.position_google is None else False
        while flag_bad_proxy:
            driver.quit()
            driver = create_new_proxy()
            search_google(driver, req_i)
            flag_bad_proxy = True if req_i.position_google is None else False
        print("\r Выполнено запросов в google: {}".format(i), end="")
    for i, req_i in enumerate(start=1, iterable=reqs):  # Запросы в yandex
        search_yandex(driver, req_i)
        lag_bad_proxy = True if req_i.position_yandex is None else False
        while lag_bad_proxy:
            driver.quit()
            driver = create_new_proxy()
            search_yandex(driver, req_i)
            lag_bad_proxy = True if req_i.position_yandex is None else False
        print("\r Выполнено запросов в yandex: {}".format(i), end="")
    driver.quit()


def start_parser():  # Запуск скрипта
    read_file_name = 'list_requests'  # read_file_name = input('filename: ')
    if 'json' in (read_file_name):
        reqs = Req.read_json(read_file_name)
    else:
        reqs = Req.read_txt(read_file_name)
    time_now = datetime.now(tz=None)
    print("time start {}:{}:{}".format(time_now.hour, time_now.minute, time_now.second))
    get_positions(reqs)  # делаем запросы в google и яндекс, отправляем список обьектов Req
    Req.create_json(reqs)
    time_now = datetime.now(tz=None)
    print("time finish {}:{}:{}".format(time_now.hour, time_now.minute, time_now.second))


if __name__ == "__main__":
    start_parser()