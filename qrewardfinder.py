from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.keys import Keys

from argparse import RawTextHelpFormatter, ArgumentParser

import datetime
import helpers
import sys

from time import sleep


def flights_worker(args, driver, travel_date, travel_class, err_count, flip_flights):
    """Flight worker
    
       Function will try to run a maximum of 3 times as the Qantas
       site can behave unusually at times it can refuse interaction
       with Selenium. This can ususally be resolved after waiting
       a few mintes and restarting
    """
    try:
        flights_found = check_flights(driver, travel_date, travel_class, args, flip_flights)
    except Exception as e:
        if err_count == 2:
            print('Maximum retries exceeded. Exiting...')
            sys.exit(0)
        else:
            print('An error has occured, trying again...')
            err_count += 1
            return flights_worker(args, driver, travel_date, travel_class, err_count, flip_flights)

    return err_count, flights_found
            

def check_flights(driver, travel_date, travel_class, args, flip_flights):
    """Main function which navigates and interacts 
       through the Qantas site
       
       Function will navigate to the flight element, default the trip type
       to One way then set iterate through the flight elemenents (runways) in
       the following order

        SELECT TRIP DETAILS:
            First element (0) is number of travellers
            Second Element (1) is departing location
            Third element (2) is destination
            Forth element (3) is travel date(s)

        NOTE: Sleeps are required as WebDriverWait wasn't playing nicely
    """
    
    flights_found = []
    driver.get('https://www.qantas.com/')
    action = ActionChains(driver)

    WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[@aria-controls='flights']"))).click()

    for i in range(2): #trip type
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[contains(@aria-label, 'Trip Type Menu')]"))).click()
        WebDriverWait(driver, 2).until(EC.element_to_be_clickable((By.XPATH, f"//*[@id='downshift-0-item-{i}']"))).click()
        try:    
            WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(@aria-label, 'Trip Type Menu, One way selected')]")))
            break
        except TimeoutException:
            continue
    
    runways = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@class, 'runway-popup-field__button')]")))
    sleep(2)

    for idx, runway in enumerate(runways):
        if idx == 0: #NUMBER OF TRAVELLERS
            action.move_to_element(runway).click().perform()
            for i in range(4):
                WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@aria-label='Decrease Value']"))).click()

            for i in range(1, args['people']):
                WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@aria-label='Increase Value']"))).click()
            
            #confirm button
            WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@class='css-vbrrm8-baseStyles-baseStyles-baseStyles-solidStyles-solidStyles-solidStyles-Button']"))).click()
            
        elif 1 <= idx <= 2: #LOCATIONS
            if not flip_flights:
                flight_text = 'Depature -'
                input_val = args['from'] if idx == 1 else args['to']
            else:
                flight_text = 'Return -'
                input_val = args['to'] if idx == 1 else args['from']
            
            action.move_to_element(runway).click().perform()
            sleep(2)
            WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@class='css-1mu1mk2']"))).send_keys(input_val)
            sleep(2)
            WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@class='css-1mu1mk2']"))).send_keys(Keys.ENTER)
        else: #TRAVEL DATE
            try:
                #remove cookie popup
                WebDriverWait(runway, 2).until(EC.element_to_be_clickable((By.XPATH, "//*[@class='optanon-alert-box-button-middle accept-cookie-container']"))).click()
            except TimeoutException:
                pass

            action.move_to_element(runway).click().perform()
            sleep(2)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(@aria-label, '{datetime.datetime.today().strftime('%a %b %d %Y')}')]"))).click()
            
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
        WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[@class='btn btn-primary qf-continue']"))).click()
    except TimeoutException:
        pass

    for key, val in travel_class.items():
        flights_found.append(f'{flight_text} {val} class flights found :D') if detect_rewards(driver, key, args['verbose']) else flights_found.append(f'{flight_text} No {val} class flights found :(')
        flights_found.extend(detect_surrounding_flights(driver))

    return flights_found


def detect_rewards(driver, travel_class, verbose):
    """Detects reward flight(s)
       
       Function will check if selenium has navigated to
       the correct travel class then determine if any
       flights contain the Qantas red ribbon indicating
       that a reward flight is available
    """
    
    if WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//*[@value='{travel_class}']"))).get_attribute('aria-selected') == 'false':
        WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, f"//*[@value='{travel_class}']"))).click()

        load_complete = False
        while not load_complete:
            load_complete = check_loading(driver)
    try:
        if verbose:
            for i in range(3):
                driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
            WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class='shape-top-right-container ng-star-inserted']")))
        else:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[@class='shape-top-right-container ng-star-inserted']")))
        return True
    except TimeoutException:
        return False


def detect_surrounding_flights(driver):
    """Detects if reward flight(s) are avaiable on a different day
       
       Function will check if the date ribbon at the top of the
       flights page contains the Qantas red ribbon indicating
       that a reward flight is available
    """

    surrounding_flights = []
    #function assumes that the correct travel class has already been selected
    cal_tabs = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//*[@class='cal-tab ng-star-inserted']")))
    for cal in cal_tabs:
        try:
            WebDriverWait(cal, 5).until(EC.presence_of_element_located((By.XPATH, ".//*[@class='price classic-rewards ng-star-inserted']")))
            flight_date = WebDriverWait(cal, 5).until(EC.presence_of_element_located((By.XPATH, ".//*[@class='date']"))).text
            surrounding_flights.append(f'Alternative reward flight found on {flight_date}')
        except TimeoutException:
            continue

    return surrounding_flights


def check_loading(driver):
    """Function will contining checking the flight loading 
       elements and return True once is drops from the page"""
    try:
        driver.find_element(By.XPATH, "//*[@class='loading-flights-text']")
    except NoSuchElementException:
        return True
    finally:
        sleep(0.3)


def arg_parser():
    """Builds argumments"""
    parser = ArgumentParser(description="""Qantas Reward Flight Finder \n\tTool currently only configured for international flights. Domestic flight functionality will be added in a future version \n\tFor detailed usage and search tips see https://github.com/funk44/QRewardFinder""", 
                                    formatter_class=RawTextHelpFormatter, prog='Reward Flight Finder')
    parser.add_argument('-f','--from', help='(Required) The airport you are travelling from (more detail is better e.g. Melbourne, Australia)', required=True, type=str, metavar='')
    parser.add_argument('-t','--to', help='(Required) The airport you are travelling to (more detail is better e.g. Singapore, Singapore)', required=True, type=str, metavar='')
    parser.add_argument('-d','--departure', help='(Required) Date of departure. Accepted formats are: YYYYMMDD, YYYY-MM-DD & DD/MM/YYYY', required=True, type=str, metavar='')
    parser.add_argument('-p','--people', help='Number of people travelling. Default is 1', required=False, default=1, type=int, metavar='')
    parser.add_argument('-c','--class', help='Travel class. Options are: 0 - Economy, 1 - Business, 2 - Economy & Business', required=False, choices={0,1,2}, default=0, type=int, metavar='')
    parser.add_argument('-r','--return', help='Return flight date. NOTE: QRFF will search for both legs indvidually', required=False, type=str, metavar='')
    parser.add_argument('-v','--verbose', help='By default QRFF will only search for the best flights, turning this on will enable a full search', required=False, action='store_true')
    
    return vars(parser.parse_args())


def validate_and_build_args(args):
    """Validates and returns and error list if incorrect arguments or
       formats have been passed.
       
       Function also builds travel class in dict required for the flight
       worker"""
    val_errors = []
    travel_dates = []

    dep_date = helpers.validate_date(args['departure'])
    if not dep_date:
        val_errors.append('Incorrect departure date format')
        return val_errors, False, False

    if not helpers.too_far_future(dep_date): val_errors.append('Departure date is too far in the future')

    travel_dates.append(dep_date)

    #return date validations
    if args['return']:
        return_date = helpers.validate_date(args['return'])
        if not return_date: 
            val_errors.append('Incorrect return date format')
            return val_errors, False, False
        
        if not helpers.check_dates(dep_date, return_date): val_errors.append('Return date is before departure date')
        if not helpers.too_far_future(return_date): val_errors.append('Return date is too far in the future')

        travel_dates.append(return_date)
        
    #build travel class into dict
    if args['class'] == 0:
        travel_class = {'ECO': 'Economy'}
    elif args['class'] == 1:
        travel_class = {'BUS': 'Business'}
    else:
        travel_class = {'ECO': 'Economy', 'BUS': 'Business'}

    return val_errors, travel_dates, travel_class


if __name__ == '__main__':
    err_count = 0
    flight_info = []
    flip_flights = False

    args = arg_parser()
    val_errors, travel_dates, travel_class = validate_and_build_args(args)
    
    if val_errors:
        print('Error(s) found in arguments:')
        for val in val_errors:
            print(f'\t{val}')
            sys.exit(0)

    driver = helpers.get_driver()

    for idx, travel_date in enumerate(travel_dates):
        if idx == 1: flip_flights = True
        err_count, flights = flights_worker(args, driver, travel_date, travel_class, err_count, flip_flights)
        flight_info.extend(flights)

    driver.quit()

    for x in flight_info:
        if not 'Alt' in x:
            print(x)
        else:
            print(f'\t{x}')