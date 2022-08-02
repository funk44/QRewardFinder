from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import datetime
import argparse
from argparse import RawTextHelpFormatter
import validations

from time import sleep

#todays date to interact with date window
today = datetime.datetime.today().strftime('%a %b %d %Y')


def worker():
    args = build_args()
    val_flag, val_errors, travel_date = validate_args(args)

    if not val_flag:
        print('Errors found in arguments:')
        for val in val_errors:
            print(f'\t{val}')
        return
    
    if check_flights(travel_date, args['to'], args['from'], args['people'], args['option']):
        print('Reward flights found')
    else:
        print('No reward flights found')


def check_flights(travel_date, travel_to, travel_from, travellers, flight_type):
    reward_found = False

    driver = uc.Chrome(use_subprocess=True)
    driver.get('https://www.qantas.com/')

    #mouse movement
    action = ActionChains(driver)

    #open the flight accordian
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[@aria-controls='flights']"))).click()

    #select the flight type
    flight_type = 'One way' if flight_type == 0 else 'Return'
    for i in range(2):
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(@aria-label, 'Trip Type Menu')]"))).click()
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, f"//*[@id='downshift-0-item-{i}']"))).click()
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
            
            for i in range(11):
                if i == 10: return
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

    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[@class='shape-top-right-container ng-star-inserted']")))
        reward_found = True
    except TimeoutException:
        pass

    driver.quit()

    return reward_found


def build_args():
    parser = argparse.ArgumentParser(description="""Qantas Reward Flight Finder \n\tTool is mostly useful for international flights but can also be used to domestic travel \n\tFor detailed usage and search tips see https://github.com/funk44/QRewardFinder""", formatter_class=RawTextHelpFormatter)
    grouper = parser.add_mutually_exclusive_group()
    parser.add_argument('-f','--from', help='The airport you are travelling from (more detail is better e.g. Melbourne, Australia)', required=True, type=str, metavar='')
    parser.add_argument('-t','--to', help='The airport you are travelling to (more detail is better e.g. Singapore, Singapore)', required=True, type=str, metavar='')
    parser.add_argument('-d','--departure', help='Date of departure. Accepted formats are: YYYYMMDD, YYYY-MM-DD & DD/MM/YYYY', required=True, type=str, metavar='')
    grouper.add_argument('-p','--people', help='Number of people travelling. Default is 1', required=False, default=1, type=int, metavar='')
    grouper.add_argument('-c','--class', help='Travel class. Options are: 0 - Economy, 1 - Business, 2 - Economy & Business', required=False, choices={0,1,2}, default=0, type=int, metavar='')
    grouper.add_argument('-o','--option', help='Flight type. Options are: 0 - One Way, 1 - Return. Default is 0 (One Way)', required=False, choices={0,1}, default=0, type=int, metavar='')
    grouper.add_argument('-r','--return', help='Return flight date. Only required if return flight selected', required=False, type=str, metavar='')
    grouper.add_argument('-e','--email', help='Schedule and alert via email. NOTE: Requires JSON to be populated with additional detail', required=False, action='store_true')
    
    return vars(parser.parse_args())


def validate_args(args):

    val_flag = True
    val_errors = []

    #dates
    travel_date = validations.validate_date(args['departure'])
    if not travel_date:
        val_errors.append('Incorrect travel date format')
        val_flag = False

    return val_flag, val_errors, travel_date

if __name__ == '__main__':
    worker()


