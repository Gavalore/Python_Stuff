import json
from datetime import datetime, timedelta
from tkinter import Tk
from tkinter.filedialog import askopenfilename
from pathlib import Path
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.select import Select


def get_current_date():
    date = datetime.now()
    return date


def format_date(date):
    return date.strftime('%Y/%m/%d %H:%M')


def set_opening_date(current_date):
    opening_date = current_date + timedelta(minutes=5)
    return format_date(opening_date)


def set_closing_date(current_date):
    closing_date = current_date + timedelta(days=3650)
    return format_date(closing_date)


# Prompt a file dialog, initialised from the parent directory, and return the full path of a selected file.
def select_file():
    print('Opening browse file dialog')
    Tk().withdraw()
    path = Path().resolve()
    file = askopenfilename(initialdir=f'{path}/payloads', filetypes=(('JSON Source File', '*.json'), ('All Files',
                                                                                                      '*.*')))
    return file


def continue_prompt():
    answer = False
    if input('Do You Want To Continue? [y/n] ').upper() == 'Y':
        print('Continuing...')
        answer = True
    return answer


def set_cycle_provider(provider, third_party_tag):
    if provider == 'Third party':
        provider = third_party_tag
    elif provider == 'Red Rake':
        provider = provider.replace(' ', '')
    return provider


def set_cycle_name(name, provider, currency):
    return f'{name} - {provider} - {currency}'


class GameDeployer:
    # Upon initialisation, create the web driver (configuring to prevent automatic closure of the window), navigate
    #  the Web Driver to the admin url, and prompt the user to select a .json file to be loaded into the  automation.
    def __init__(self):
        print('Initialising GameDeployer')
        opts = Options()
        opts.add_experimental_option('detach', True)
        self._url = 'REDACTED'
        self._test = True
        self.browser = Chrome(options=opts)
        self.browser.get(self._url)
        self.data = json.load(open(select_file()))

    # GETTERS/SETTERS
    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        self._url = url

    @property
    def test(self):
        return self._test

    @test.setter
    def test(self, test):
        self._test = test

    # Stop the WebDriver from proceeding until the presence of an element is found using XPATH.
    def wait_for_element(self, xpath):
        element = WebDriverWait(self.browser, 60).until(
            ec.presence_of_element_located((By.XPATH, f'{xpath}')))
        return element

    def populate_element(self, xpath, value):
        element = self.wait_for_element(xpath)
        element.send_keys(value)

    def click_element(self, xpath):
        element = self.wait_for_element(xpath)
        element.click()

    def select_from_list(self, xpath, value):
        select = Select(self.wait_for_element(xpath))
        return select.select_by_visible_text(value)

    def submit_text_element(self, xpath):
        element = self.wait_for_element(xpath)
        element.send_keys(Keys.RETURN)

    def search_for_game(self, xpath, game):
        self.populate_element(xpath, game)
        self.submit_text_element(xpath)

    # Return the XPATH of the parent element of a table row, for use in selecting the action buttons on a given row.
    def search_for_table_row(self, value):
        xpath = f'//tr[.//text()="{value}"]'
        element = self.wait_for_element(xpath)
        return xpath

    # Using the XPATH from search_for_table_row(), construct an valid XPATH that will locate the child action of a
    # given parent.
    def click_table_row_view_action(self, row, action):
        par_xpath = row
        child_xpath = f'/td/a[@class="{action}"]'
        xpath = par_xpath + child_xpath
        element = self.wait_for_element(xpath)
        element.click()

    # Navigate to the login page, populate the form fields with the user's credentials and submit.
    def login(self, user, passwd):
        print('Starting login process...')
        self.populate_element('//*[@id="APILoginForm_APILoginForm_username"]', user)
        self.populate_element('//*[@id="APILoginForm_APILoginForm_password"]', passwd)
        self.populate_element('//*[@id="APILoginForm_APILoginForm_customerShortName"]', 'twelve40')
        self.click_element('//*[@id="APILoginForm_APILoginForm_action_submit"]')
        self.wait_for_element('//*[@id="container"]/header/div[2]/ul/li[4]/a')

    # Navigate to the Instant Win screen. Loop through each instant win from the selected payload, and submit the
    # populated form
    def create_instant_wins(self):
        print('Creating instant wins..')
        for game in self.data:
            self.click_element('//*[@id="container"]/header/div[2]/ul/li[4]/a')
            self.click_element('//*[@id="ajax-tab-content"]/div[2]/div/div[2]/a[2]')
            self.browser.implicitly_wait(1)
            self.populate_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_name"]',
                                  game['name'])
            self.populate_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_description"]',
                                  game['description'])
            self.populate_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_externalGameId"]',
                                  game['external_gameid'])
            self.select_from_list('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_provider"]',
                                  game['provider'])
            self.populate_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_providerTag"]',
                                  game['third_party_provider_tag'])
            self.populate_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_rtp"]',
                                  game['rtp'])
            self.populate_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_category"]',
                                  game['category'])
            self.select_from_list('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_instantWinLanguages"]',
                                  'English (British)')
            self.select_from_list('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_instantWinCurrencies"]',
                                  'GBP - British Pound')
            self.click_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_enabled"]')

            if continue_prompt():
                if self._test:
                    self.click_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm"]/div/div/div[3]/button')
                else:
                    self.click_element('//*[@id="ExternalInstantWinForm_ExternalInstantWinForm_action_submit"]')
                    self.click_element('//*[@id="Form_CustomerForm_Customer_4704cbb1-7dad-4a24-b173-2ec258125a2a"]')
                    self.click_element('//*[@id="Form_CustomerForm_Customer_ecf5b735-31bc-4287-a528-606a2f0c9fe6"]')
                    self.click_element('//*[@id="Form_CustomerForm_action_processCustomerForm"]')
            else:
                break

    def navigate_to_customer(self, customer):
        self.click_element('//*[@id="container"]/header/div[2]/ul/li[1]/a')
        row = self.search_for_table_row(customer)
        self.click_table_row_view_action(row, 'btn btn-info')
        print(f'Navigating to customer: {customer}')

    def approve_instant_win(self):
        print('Transitioning status of Instant Win to Approved...')
        self.click_element('//*[@id="main-content"]/section/div[2]/div[2]/div[1]/div/div[2]/a[1]')
        self.click_element('//*[@id="main-content"]/section/div[2]/div[2]/div[1]/div/div[2]/a[1]')
        self.click_element('//*[@id="main-content"]/section/div[2]/div[2]/div[1]/div/div[2]/a[1]')

    def navigate_to_admin_menu(self):
        print('Navigating to Admin Menu...')
        self.click_element('//*[@id="container"]/header/div[2]/ul/li[12]/a')
        self.click_element('//*[@id="container"]/header/div[2]/ul/li[12]/ul/li[5]/a')
        self.wait_for_element('//*[@id="main-content"]/section/div[2]/div[1]/section/div')

    def create_customer_instant_win_cycles(self, currency):
        print('Creating customer level instant win cycles...')
        opening_time = set_opening_date(get_current_date())
        closing_time = set_closing_date(get_current_date())
        for game in self.data:
            provider = set_cycle_provider(game['provider'], game['third_party_provider_tag'])
            cycle_name = set_cycle_name(game['name'], provider, currency)
            cycle_config = f'EXTERNAL {currency}'
            self.click_element('//*[@id="container"]/header/div[2]/ul/li[8]/a')
            self.click_element('//*[@id="container"]/header/div[2]/ul/li[8]/ul/li[2]/a')
            self.click_element('//*[@id="ajax-tab-content"]/div[3]/div/div[2]/a')
            self.browser.implicitly_wait(1)
            self.populate_element('//*[@id="InstantWinCycleForm_InstantWinCycleForm_name"]',
                                  cycle_name)
            self.populate_element('//*[@id="InstantWinCycleForm_InstantWinCycleForm_opening"]',
                                  opening_time)
            self.populate_element('//*[@id="InstantWinCycleForm_InstantWinCycleForm_closing"]',
                                  closing_time)
            self.click_element('//*[@id="InstantWinCycleForm_InstantWinCycleForm_external"]')
            self.select_from_list('//*[@id="tryCycleConfig"]',
                                  cycle_config)
            self.select_from_list('//*[@id="cycleConfig"]',
                                  cycle_config)
            if continue_prompt():
                if self._test:
                    self.click_element('//*[@id="InstantWinCycleForm_InstantWinCycleForm"]/div/div/div[3]/button')
                else:
                    self.click_element('//*[@id="InstantWinCycleForm_InstantWinCycleForm"]/div/div/div[3]/button')
                    self.click_element('//*[@id="InstantWinCycleForm_InstantWinCycleForm_action_submit"]')
                    self.approve_instant_win()
            else:
                break

    # For each instant win from the payload, navigate to the instant win page for each game, map the corresponding
    # cycle and mark the new cycle as the current cycle. In test mode, the cycle name will be set as an existing cycle
    # and the updates will NOT be submitted.
    def map_cycles_to_instant_wins(self, currency):
        print('Mapping cycles to instant wins...')
        for game in self.data:
            if self._test:
                if currency == 'GBP':
                    cycle_name = 'Halloween Wins - RedRake - GBP'
                else:
                    cycle_name = 'Halloween Wins - RedRake - USD'
            else:
                provider = set_cycle_provider(game['provider'], game['third_party_provider_tag'])
                cycle_name = set_cycle_name(game['name'], provider, currency)
            self.click_element('//*[@id="container"]/header/div[2]/ul/li[8]/a')
            self.click_element('//*[@id="container"]/header/div[2]/ul/li[8]/ul/li[1]/a')
            self.search_for_game('//*[@id="game-skins_filter"]/label/input', game['name'])
            self.click_table_row_view_action(self.search_for_table_row(game['name']), 'btn btn-info')
            self.select_from_list('//*[@id="Form_AddCycleForm_cycleId"]', cycle_name)
            if continue_prompt():
                if self._test:
                    continue
                else:
                    self.click_element('//*[@id="Form_AddCycleForm_action_processAddCycleForm"]')
                    self.click_element(
                        '//*[@id="main-content"]/section/div[4]/div/section/div/div/table/tbody/tr/td[5]/a[1]')
                continue
            else:
                break


print('Starting game deployment automation...')
client = GameDeployer()
if input('Is this an test? [y/n] ').upper() == 'N':
    client.test = False
    print('Automation has been set to submit populated forms...')
else:
    print('Automation has been set to Test mode. Populated forms will not be submitted, and instead cancelled...')
username = input("Please input your username. ")
password = input("Please input your password. ")
client.login(username, password)
client.create_instant_wins()
client.navigate_to_customer('LottoSite')
client.create_customer_instant_win_cycles('GBP')
client.map_cycles_to_instant_wins('GBP')
client.navigate_to_admin_menu()
client.navigate_to_customer('LottoSite2')
client.create_customer_instant_win_cycles('USD')
client.map_cycles_to_instant_wins('USD')
print('The automation has completed without error...')
