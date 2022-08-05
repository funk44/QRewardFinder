from datetime import datetime

def validate_date(date_val):
    for fmt in ('%Y%m%d', '%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(date_val, fmt).strftime('%a %b %d %Y')
        except ValueError:
            pass
    return False
