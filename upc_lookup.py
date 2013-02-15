import urllib2
from pprint import pprint

from bs4 import BeautifulSoup

from pyquery import PyQuery

from factual import Factual


# def look_up_upc(upc):
#     url = 'http://www.upcdatabase.com/item/'+upc
#     req = urllib2.Request(url)
#     response = urllib2.urlopen(req)
#     page = PyQuery(response.read())

#     for label_row in page.find('table.data tr td:first-child'):
#         label_row = PyQuery(label_row)
#         if label_row.text() == "Description":
#             description_cell = label_row.siblings()[-1]
#             return description_cell.text


#http://api.v3.factual.com/t/products-cpg?filters={"upc":"611269991000"}


def look_up_upc(upc):
    factual = Factual(
        '1psULPx7BQfmamX3bnkOnR7NWkcPRKcjnSvazvXF'
        , 'Eu8sIGOyXIPrq3jHAudGjkPea4v5v813jJcxOOTW'
    )

    q = factual.table('products-cpg').filters({"upc":"611269991000"})

    result = q.data()[0]
    return "{brand} - {product_name}". format(**result)




print look_up_upc('611269991000')
