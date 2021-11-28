import datetime as dt


def year(request):
    """Добавляет переменную с текущим годом."""
    today_year = dt.datetime.now().date().year
    return {
        'year': today_year
    }
