from datetime import datetime
from dateutil.relativedelta import relativedelta
import undetected_chromedriver as uc


def validate_date(date_val):
    for fmt in ('%Y%m%d', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_val, fmt).strftime('%a %b %d %Y')
        except ValueError:
            pass
    return False


def check_dates(dep, ret):
    if datetime.strptime(ret, '%a %b %d %Y') < datetime.strptime(dep, '%a %b %d %Y'):
        return False
    else:
        return True


def too_far_future(travel_date):
    max_date = datetime.today() + relativedelta(months=12)
    if datetime.strptime(travel_date, '%a %b %d %Y') > max_date:
        return False
    else:
        return True


def webdriver_options():
    options = uc.ChromeOptions()
    # options.headless=True
    # options.add_argument('--ignore-certificate-errors')
    # options.add_argument('--headless')

    return uc.Chrome(use_subprocess=True,options=options)