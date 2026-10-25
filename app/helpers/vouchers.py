from datetime import date


def voucher_is_usable(voucher, today=None):
    '''A voucher can only be applied while it is switched on and today is
    inside its start/end dates (both days included). Checked wherever a
    voucher is previewed or charged, so an expired or deactivated code can
    never reduce a price.'''
    if voucher is None:
        return False
    if str(voucher.is_active) != 'True':
        return False
    today = today or date.today()
    if voucher.start_date and today < voucher.start_date:
        return False
    if voucher.end_date and today > voucher.end_date:
        return False
    return True
