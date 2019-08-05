from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from stem import Signal
from stem.control import Controller


class Browser(webdriver.Firefox):

    def __init__(self, ports=(9050, 9051), headless=True, languages='ru'):
        opts = Options()
        opts.headless = headless  # True -- без графического интерфейса
        profile = webdriver.FirefoxProfile()  # ='/home/sergey/PycharmProjects/crm_parser/ProfileFireFox'
        profile.set_preference("network.proxy.type", 1)
        profile.set_preference("network.proxy.socks", '127.0.0.1')
        profile.set_preference("network.proxy.socks_port", ports[0])
        profile.set_preference("network.proxy.socks_remote_dns", False)
        profile.set_preference("intl.accept_languages", languages)
        profile.set_preference("network.cookie.cookieBehavior", 0)
        profile.update_preferences()
        super().__init__(firefox_profile=profile, options=opts)
        self.use_proxy_port, self.control_proxy_port = ports

    def restart_proxy(self):
        with Controller.from_port(port= self.control_proxy_port) as controller:
            controller.authenticate()
            controller.signal(Signal.NEWNYM)