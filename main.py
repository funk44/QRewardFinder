from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver import ActionChains
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
import undetected_chromedriver as uc
import yagmail
import datetime

from time import sleep

tofrom = ['MEL', 'SIN']
flight_type = 'One way'
travel_date = 'Thu Apr 13 2023'

#todays date to interact with date window
today = datetime.datetime.today().strftime('%a %b %d %Y')

def check_flights():
    reward_found = False

    driver = uc.Chrome(use_subprocess=True)
    driver.get('https://www.qantas.com/')

    #mouse movement
    action = ActionChains(driver)

    #open the flight accordian
    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[@aria-controls='flights']"))).click()

    #select the flight type
    for i in range(2):
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//*[contains(@aria-label, 'Trip Type Menu')]"))).click()
        WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, f"//*[@id='downshift-0-item-{i}']"))).click()
        try:    
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(@aria-label, 'Trip Type Menu, {flight_type} selected')]")))
            break
        except TimeoutException:
            continue
    
    """ 
    SELECT TRIP DETAILS:
        First element is number of travlellers
        Second Element is departing location
        Third element is destination
        Forth element is travel dates
    """

    #get list of runway elements
    runways = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, "//*[contains(@class, 'runway-popup-field__button')]")))

    for idx, runway in enumerate(runways):
        #select number of people
        if idx == 0:
            continue

        #qantas likely has some detection that doesn't recognise inputting text so the element must be moved to. NOTE: sleeps are required
        elif 1 <= idx <= 2:
            input_val = 0 if idx == 1 else 1
            action.move_to_element(runway).click().perform()
            sleep(2)
            WebDriverWait(runway, 5).until(EC.presence_of_element_located((By.XPATH, "//*[@class='css-1mu1mk2']"))).send_keys(tofrom[input_val])
            sleep(2)
            WebDriverWait(runway, 5).until(EC.presence_of_element_located((By.XPATH, "//*[@class='css-1mu1mk2']"))).send_keys(Keys.ENTER)
        else:
            #click the cookies button if its in the way
            try:
                WebDriverWait(runway, 2).until(EC.presence_of_element_located((By.XPATH, "//*[@class='optanon-alert-box-button-middle accept-cookie-container']"))).click()
            except TimeoutException:
                pass

            action.move_to_element(runway).click().perform()

            #move within date window
            sleep(2)

            #click on today twice to interact with the date menu
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(@aria-label, '{today}')]"))).click()
            
            for i in range(11):
                if i == 10: return
                try:
                    driver.execute_script("arguments[0].scrollIntoView();", driver.find_element(By.XPATH, f"//*[contains(@aria-label, '{travel_date}')]"))
                    WebDriverWait(runway, 1).until(EC.presence_of_element_located((By.XPATH, f"//*[contains(@aria-label, '{travel_date}')]"))).click()
                    break
                except (TimeoutException, NoSuchElementException):
                    driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.PAGE_DOWN)
                    continue

            sleep(1)
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[contains(@data-testid, 'dialogConfirmation')]"))).click()

    WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//*[@class='submit-btn']"))).click()

    try:
        WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, "//*[@class='shape-top-right-container ng-star-inserted']")))
        reward_found = True
    except TimeoutException:
        pass

    driver.quit()

    return reward_found


def send_gmail():
    #create message
    message = f'Flights found from {tofrom[0]} to {tofrom[1]} on {travel_date}'

    yag = yagmail.SMTP('benmabolton@gmail.com', 'sfmmjcwscbgedwjz')
    yag.send(to='bmbolton@tpg.com.au', subject='Reward flights found', contents=message)


if __name__ == '__main__':
    if check_flights():
        send_gmail()
    else:
        print('No reward flights found')


