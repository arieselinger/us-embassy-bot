from selenium import webdriver
from selenium.webdriver.firefox.options import Options

import time
import datetime
import json
import requests
import dateparser
import locale
import smtplib

browser = None


def log(message, clear=False):
    """
    Logs a message with the current date

    :param message: message to print
    :param clear: True if the message should be overwritten by the next one. Default: False.
    """
    print(f'[{str(datetime.datetime.now())}] {message}', end=('\r' if clear else '\n'))


def sleep(n):
    """
    Waits for n seconds

    :param n: Number of seconds to pause
    """
    for i in range(n, 0, -1):
        log(f"Waiting {i} s...", clear=True)
        time.sleep(1)


def login_and_get_cookies(username, password, appointment_number, headless):
    """
    Uses Selenium to access *https://ais.usvisa-info.com*

    :param username: US Embassy username (https://ais.usvisa-info.com)
    :param password: US Embassy password
    :param appointment_number: Appointment number (e.g. 31490174)
    :param headless: should be set to False for debugging
    :return: cookies as a header for the API
    """
    global browser

    if browser:
        browser.quit()
        browser = None
        log('Killing previous webdriver.')
        sleep(5)

    options = Options()
    options.headless = headless
    profile = webdriver.FirefoxProfile()
    profile.set_preference("browser.cache.disk.enable", False)
    profile.set_preference("browser.cache.memory.enable", False)
    profile.set_preference("browser.cache.offline.enable", False)
    profile.set_preference("network.http.use-cache", False)
    browser = webdriver.Firefox(profile, options=options)
    browser.delete_all_cookies()

    # Go to main page
    log('Going to main page.')
    browser.get(f'https://ais.usvisa-info.com/fr-fr/niv/schedule/{appointment_number}/appointment')
    sleep(5)

    # Click on 'OK' button if needed
    try:
        ok_elt = browser.find_element_by_xpath('/html/body/div[6]/div[3]/div/button')
        ok_elt.click()
        sleep(5)
    except:
        pass

    # Try to login
    user_elt = browser.find_element_by_id('user_email')
    password_elt = browser.find_element_by_id('user_password')
    condition_elt = browser.find_element_by_xpath(
        '/html/body/div[5]/main/div[3]/div/div[1]/div/form/div[3]/label/div')
    login_elt = browser.find_element_by_xpath(
        "/html/body/div[5]/main/div[3]/div/div[1]/div/form/p[1]/input")
    log('Trying to log in.')
    user_elt.send_keys(username)
    password_elt.send_keys(password)
    condition_elt.click()
    login_elt.click()

    # Get credentials
    sleep(5)
    log('Getting credentials.')
    cookies = {}  # Should contain '_yatri_session', '_ga' and '_gid'
    for cookie in browser.get_cookies():
        if cookie.get('name'):
            cookies[cookie.get('name')] = cookie.get('value')
    sleep(5)

    return cookies


def get_new_appointment_date(credentials, appointment_number):
    """
    Requests the earliest appointment date
    :param credentials: cookies for the login_and_get_cookies function
    :param appointment_number: Appointment number
    :return: date
    """
    log('Seeking an earlier appointment.')
    request_url = f'https://ais.usvisa-info.com/fr-fr/niv/schedule/{appointment_number}/appointment/days/44.json'
    headers = {
        'Host': 'ais.usvisa-info.com',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:94.0) Gecko/20100101 Firefox/94.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Cache-Control': 'max-age=0'
    }
    response = requests.get(request_url, headers=headers, cookies=credentials)
    response = response.json()[0]['date']
    return response


def send_email(sender_name, user, pwd, recipient, subject, body):
    receiver = recipient if type(recipient) is list else [recipient]
    message = "From: " + sender_name + "\nTo: " + (
        ", ".join(receiver)) + "\nSubject: " + subject + "\n\n" + body + "\n"
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(user, pwd)
        server.sendmail(user, receiver, message)
        server.close()
    except Exception as e:
        log("Unable to send an email. " + str(e))


def main():
    # Read config file
    with open('config.json') as fi:
        config = json.load(fi)

    # Get credentials
    username = config['embassy']['username']
    password = config['embassy']['password']
    appointment_number = config['embassy']['appointment_number']
    headless = config['webdriver']['headless']
    credentials = login_and_get_cookies(username, password, appointment_number, headless)
    log('Connected with success.')

    # Get a new appointment date
    earliest_availability = None

    while True:
        try:
            new_date = get_new_appointment_date(credentials, appointment_number)
            locale.setlocale(locale.LC_TIME, config['msg_lang'])
            if not earliest_availability or dateparser.parse(new_date) != dateparser.parse(
                    earliest_availability):
                if config['msg_lang'] == 'fr_FR':
                    formatted_date = dateparser.parse(new_date).strftime('%A %e %B %G')
                    msg = f"Nouveau rendez-vous disponible le {formatted_date}."
                else:
                    formatted_date = dateparser.parse(new_date).strftime('%A, %e %B %G')
                    msg = f"New appointment available at the US Embassy {formatted_date}."
                log("Sending a notification - {}".format(msg))
                send_email(config['email_notification']['sender']['name'],
                           config['email_notification']['sender']['username'],
                           config['email_notification']['sender']['password'],
                           config['email_notification']['recipient'],
                           "Nouveau rendez-vous disponible!" if config['msg_lang'] == 'fr_FR' else
                           "New appointment available!",
                           msg)
                earliest_availability = new_date
            sleep(30)

        except Exception as e:
            is_connected = False
            log("Exception: " + str(e))
            while not is_connected:
                try:
                    credentials = login_and_get_cookies(username, password, appointment_number,
                                                        headless)
                    log('Connected with success.')
                    is_connected = True
                except Exception as e:
                    log('Unable to log in. Try again in 5 s.' + str(e))
                    sleep(5)


if __name__ == "__main__":
    main()
