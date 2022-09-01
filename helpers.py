from datetime import datetime
from dateutil.relativedelta import relativedelta
from pathlib import Path
import undetected_chromedriver as uc
from pathlib import Path
from fake_useragent import UserAgent


def validate_date(date_val):
    """Validate the correct date format
       has been passed to argparse"""
    for fmt in ('%Y%m%d', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_val, fmt).strftime('%a %b %d %Y')
        except ValueError:
            pass
    return False


def check_dates(dep, ret):
    """Checks if the return date is after the departure date"""
    if datetime.strptime(ret, '%a %b %d %Y') < datetime.strptime(dep, '%a %b %d %Y'):
        return False
    return True


def too_far_future(travel_date): 
    """Checks if the flight is no longer
       that 1 year in the future due to
       limitations on the Qantas site"""
    max_date = datetime.today() + relativedelta(months=12)
    if datetime.strptime(travel_date, '%a %b %d %Y') > max_date:
        return False
    return True


def get_driver():
    """Returns headless chromedriver"""
    ua = UserAgent()
    user_agent = ua.random

    options = uc.ChromeOptions()
    options.add_argument(f'user-agent={user_agent}')

    #options.headless = True
    # options.add_argument("--window-size=1920,1080")
    # options.add_argument("start-maximized")


    return uc.Chrome(use_subprocess=True, options=options, suppress_welcome=True)
