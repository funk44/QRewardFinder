from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from argparse import RawTextHelpFormatter, ArgumentParser

import undetected_chromedriver as uc
import datetime
import helpers

from pathlib import Path
from time import sleep

#todays date to interact with date window
today = datetime.datetime.today().strftime('%a %b %d %Y')

driver_path = Path(__file__).parent


def worker():
    args = build_args()
    val_errors, travel_date, travel_class = validate_and_build_args(args)

    if val_errors:
        print('Errors found in arguments:')
        for val in val_errors:
            print(f'\t{val}')
        return
    
    returns = check_flights(travel_date, args['to'], args['from'], args['people'], args['option'], travel_class)
    for x in returns:
        print(x)

 
def check_flights(travel_date, travel_to, travel_from, travellers, flight_type, travel_class):
    flights_found = []

    driver = uc.Chrome(use_subprocess=True)
    driver.get('https://www.qantas.com/')

    #mouse movement
    action = ActionChains(driver)

    #open the flight accordian
    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-controls='flights']"))).click()

    #select the flight type
    flight_type = 'One way' if flight_type == 0 else 'Return'
    for i in range(2):
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@aria-label, 'Trip Type Menu')]"))).click()
        WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='downshift-0-item-{i}']"))).click()
        try:    
            WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(@aria-label, 'Trip Type Menu, {flight_type} selected')]")))
            break
        except TimeoutException:
            continue
    
    #get list of runway elements
    runways = WebDriverWait(driver, 2).until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@class, 'runway-popup-field__button')]")))

    for idx, runway in enumerate(runways):
        """ 
        SELECT TRIP DETAILS:
            First element (0) is number of travellers
            Second Element (1) is departing location
            Third element (2) is destination
            Forth element (3) is travel dates
        """
        if idx == 0:
            action.move_to_element(runway).click().perform()
            #loop over and set value to one
            for i in range(4):
                WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@aria-label='Decrease Value']"))).click()

            for i in range(1, travellers):
                WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@aria-label='Increase Value']"))).click()
            
            #confirm button
            WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@class='css-vbrrm8-baseStyles-baseStyles-baseStyles-solidStyles-solidStyles-solidStyles-Button']"))).click()
            
        #NOTE: sleeps are required or site won't recognise input, WebDriverWait wasn't playing nicely nor was element_to_be_clickable
        elif 1 <= idx <= 2:
            input_val = travel_from if idx == 1 else travel_to
            action.move_to_element(runway).click().perform()
            sleep(2)
            WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@class='css-1mu1mk2']"))).send_keys(input_val)
            sleep(2)
            WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@class='css-1mu1mk2']"))).send_keys(Keys.ENTER)
        else:
            #select travel dates
            try:
                #remove cookie popup
                WebDriverWait(runway, 2).until(EC.element_to_be_clickable((By.XPATH, "//*[@class='optanon-alert-box-button-middle accept-cookie-container']"))).click()
            except TimeoutException:
                pass

            action.move_to_element(runway).click().perform()
            sleep(2)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(@aria-label, '{today}')]"))).click()
            
            for i in range(10):
                if i == 9: return
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.XPATH, f"//*[contains(@aria-label, '{travel_date}')]"))
                    WebDriverWait(runway, 1).until(EC.element_to_be_clickable((By.XPATH, f"//*[contains(@aria-label, '{travel_date}')]"))).click()
                    break
                except (TimeoutException, NoSuchElementException):
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    continue

            sleep(1)
            WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@data-testid, 'dialogConfirmation')]"))).click()

    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[@class='submit-btn']"))).click()

    #continue on currency prompt
    try:
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@class='btn btn-primary qf-continue']"))).click()
    except TimeoutException:
        pass

    for key, val in travel_class.items():
        flights_found.append(f'{val} class flights found :D') if detect_rewards(driver, key) else flights_found.append(f'No {val} class flights found :(')

    driver.quit()

    return flights_found


def detect_rewards(driver, travel_class):

    #check if you are already on the right page, otherwise navigate to the correct flight class
    if WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//*[@value='{travel_class}']"))).get_attribute('aria-selected') == 'false':
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//*[@value='{travel_class}']"))).click()

        load_complete = False
        while not load_complete:
            load_complete = check_loading(driver)

    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[@class='shape-top-right-container ng-star-inserted']")))
        return True
    except TimeoutException:
        return False


def check_loading(driver):
    try:
        driver.find_element(By.XPATH, "//*[@class='loading-flights-text']")
    except NoSuchElementException:
        return True
    finally:
        sleep(0.3)


def build_args():
    parser = ArgumentParser(description="""Qantas Reward Flight Finder \n\tTool is mostly useful for international flights but can also be used for domestic travel \n\tFor detailed usage and search tips see https://github.com/funk44/QRewardFinder""", 
                                    formatter_class=RawTextHelpFormatter, prog='Reward Flight Finder')
    grouper = parser.add_mutually_exclusive_group()
    parser.add_argument('-f','--from', help='(Required) The airport you are travelling from (more detail is better e.g. Melbourne, Australia)', required=True, type=str, metavar='')
    parser.add_argument('-t','--to', help='(Required) The airport you are travelling to (more detail is better e.g. Singapore, Singapore)', required=True, type=str, metavar='')
    parser.add_argument('-d','--departure', help='(Required) Date of departure. Accepted formats are: YYYYMMDD, YYYY-MM-DD & DD/MM/YYYY', required=True, type=str, metavar='')
    grouper.add_argument('-p','--people', help='Number of people travelling. Default is 1', required=False, default=1, type=int, metavar='')
    grouper.add_argument('-c','--class', help='Travel class. Options are: 0 - Economy, 1 - Business, 2 - Economy & Business', required=False, choices={0,1,2}, default=0, type=int, metavar='')
    grouper.add_argument('-o','--option', help='Flight type. Options are: 0 - One Way, 1 - Return. Default is 0 (One Way)', required=False, choices={0,1}, default=0, type=int, metavar='')
    grouper.add_argument('-r','--return', help='Return flight date. Only required if return flight selected', required=False, type=str, metavar='')
    grouper.add_argument('-v','--verbose', help='By default QRFF will only search for the best flights, turning this on will enable a full search', required=False, action='store_true')
    grouper.add_argument('-e','--email', help='Schedule and alert via email. NOTE: Requires JSON to be populated with additional detail', required=False, action='store_true')
    
    return vars(parser.parse_args())


def validate_and_build_args(args):
    val_errors = []

    #dates
    travel_date = helpers.validate_date(args['departure'])
    if not travel_date:
        val_errors.append('Incorrect travel date format')

    #travel class NOTE: will be extended to other classes
    if args['class'] == 0:
        travel_class = {'ECO': 'Economy'}
    elif args['class'] == 1:
        travel_class = {'BUS': 'Business'}
    else:
        travel_class = {'ECO': 'Economy', 'BUS': 'Business'}

    return val_errors, travel_date, travel_class


if __name__ == '__main__':
    worker()