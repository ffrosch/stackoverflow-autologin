import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager  # type: ignore

# load username and password
load_dotenv()


class StackSite(Enum):
    askubuntu = "askubuntu"
    serverfault = "serverfault"
    stackoverflow = "stackoverflow"
    gis = "gis.stackexchange"


@dataclass
class Account:
    @staticmethod
    def credentials() -> Tuple[Optional[str], Optional[str], Optional[str]]:
        email: Optional[str] = os.environ.get("STACK_EMAIL")
        password: Optional[str] = os.environ.get("STACK_PASS")
        name: Optional[str] = os.environ.get("STACK_NAME")

        if None in (email, password, name):
            raise ValueError(
                "Set 'STACK_EMAIL' 'STACK_PASS' 'STACK_NAME' env variable "
                "to successfully log into a Stack-Website"
            )

        return (email, password, name)


class Driver:
    def __init__(self):
        # Define Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")

        # Load Chrome driver with options
        self.driver: str = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options,
        )

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.driver.close()


@dataclass
class Website:

    _website: Optional[StackSite] = None

    def __init__(self, site: StackSite, account: Account, driver: Driver):
        self.driver = driver.driver
        self.website = site
        self.email, self.password, self.name = account.credentials()

    @property
    def url(self):
        return f"https://{self.website}.com"

    @property
    def website(self):
        return self._website.value

    @website.setter
    def website(self, site: StackSite):
        self._website = site
        self.load()

    def load(self):
        print(f"Visiting {self.url}")
        self.driver.get(self.url)

    @property
    def is_logged_in(self):
        try:
            self.driver.find_element(By.PARTIAL_LINK_TEXT, self.name)
        except NoSuchElementException:
            return False
        return True

    def login(self):
        print(f"Logging into {self.website}")
        self.driver.find_element(By.LINK_TEXT, "Log in").click()
        self.driver.find_element(By.ID, "email").send_keys(self.email)
        self.driver.find_element(By.ID, "password").send_keys(self.password)
        self.driver.find_element(By.ID, "submit-button").submit()
        print(f"Successfully logged into {self.website}")

    def profile_page(self):
        # Check whether login was successful
        profile = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, self.name))
        )
        profile.click()
        elem = WebDriverWait(self.driver, 5).until(
            EC.presence_of_element_located(
                (By.ID, "js-daily-access-calendar-container")
            )
        )
        print(f"Accessed profile page on {self.website} - {elem.text}")


def visit_all():
    account = Account()
    with Driver() as driver:
        for site in StackSite:
            website = Website(site, account, driver)
            if not website.is_logged_in:
                website.login()
            website.profile_page()


if __name__ == "__main__":
    visit_all()
