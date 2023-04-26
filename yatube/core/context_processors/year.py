from datetime import date


def year(request):
    current_year = date.today()
    return {'year': current_year.year}
