#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from datetime import datetime
import argparse
import json

from utils.google_email import send_email, send_text

import os
import logging
logging.basicConfig(filename=os.path.dirname(os.path.abspath(__file__)) + '/output.log', level=logging.INFO,
                    format='%(asctime)s %(message)s')


class RepFitnessBot:
    def __init__(self, headless):
        chrome_options = webdriver.ChromeOptions()
        if headless:
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument("--disable-extensions")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.wait = WebDriverWait(self.driver, 10)

        self.available = []

        self.data = self.read_file(os.path.dirname(
            os.path.abspath(__file__)) + '/data.json')

        for item in self.data:
            self.get_available(item)

        self.write_file(os.path.dirname(
            os.path.abspath(__file__)) + '/data.json', self.data)

        self.email()

    def __del__(self):
        logging.info('\n')
        self.driver.quit()

    def read_file(self, filename):
        with open(filename) as json_file:
            data = json.load(json_file)
        return data

    def write_file(self, filename, data):
        with open(filename, 'w') as json_file:
            json.dump(data, json_file, indent=4)

    def get_available(self, item):
        available = False
        self.driver.get(item['url'])
        self.wait.until(EC.presence_of_element_located(
            (By.CLASS_NAME, "stock")))
        if item['text']:
            tr = self.driver.find_element_by_xpath(
                "//strong[text()='{}']/../..".format(item['text']))
            if tr.get_attribute('class') != 'out-of-stock':
                available = True
        else:
            div = self.driver.find_element_by_xpath("//div[@title='Availability']")
            if 'unavailable' not in div.get_attribute('class'):
                available = True

        if available:
            if not item['available']:
                self.available.append(item)
            logging.info('{} - AVAILABLE'.format(item['name']))
        else:
            logging.info('{} - not available'.format(item['name']))
        item['available'] = available

    def email(self):
        if not self.available:
            return

        subject = 'RepFitness | {}/{} Available'.format(
            len(self.available), len(self.data))

        body = ''
        text_body = ''
        for item in self.available:
            body += item['name'] + '\n' + item['url'] + '\n\n'
            text_body += item['name'] + '\n'

        send_email(subject, body)
        send_text(subject, text_body)


if __name__ == '__main__':
    print(datetime.now().strftime("\n%m/%d/%Y %H:%M:%S"))
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true",
                        help="Run without window")
    flags = parser.parse_args()

    RepFitnessBot(flags.headless)
