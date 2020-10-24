from pyquery import PyQuery as pq
import json
import requests


TEMPLATE_PAGE_URL = 'https://wybory2007.pkw.gov.pl/SJM/PL/WYN/W/{}'


def getFileFromURL(url):
    # NOTE: Had to use 'requests' library as pyquery don't support
    #       '..' in URL path.
    return requests.get(url, allow_redirects=True).content
    
def convertToProperType(val):
    try:
        return int(val)
        
    except ValueError:
        try:
            return float(val)
            
        except ValueError:
            return val

def enumerateChild(parent_pq, data=None):
    table_ltr = parent_pq('td.mapltr > table')
    table_s0 = parent_pq('table #s0')
    table_s1 = parent_pq('table #s1')
    
    if table_ltr.length == 0 or \
        table_s0.length == 0 or \
        table_s1.length == 0:
        return
    
    # Parse first table
    child_name = table_ltr('tr:first').text().strip()
    if data is None:
        data = {}
    data[child_name] = []
    def parse_ltr(i, element):
        nonlocal data, child_name
    
        tr = pq(element)
        
        if (tr('td').length == 2):
            ltr_data_key = tr('td:nth-child(1)').text().strip()
            ltr_data_value = convertToProperType(tr('td:nth-child(2)').text().strip())
            
            data[child_name][0][ltr_data_key] = ltr_data_value
        
        return True
    
    data[child_name].append({})
    table_ltr('tr').each(parse_ltr)
    
    
    # Parse second table with id s0
    s0_data_header = ['Numer listy', 
                      'Nazwa komitetu wyborczego',
                      'Liczba głosów na listę',
                      'Liczba głosów: na listę / ważnych [%]']
    def parse_s0_data(i, element):
        nonlocal s0_data_header, data, child_name
        
        tr = pq(element)
        
        if tr('td:nth-child(1)').text().strip().isnumeric():
            data[child_name][1].append({})
            
            def parse_tds(i1, element1):
                nonlocal s0_data_header, data, child_name, i
                
                tr = pq(element1)
                
                if i1 > 3:
                    return False
                    
                data[child_name][1][-1][s0_data_header[i1]] = \
                    convertToProperType(tr('td:nth-child({})'.format(i1+1)).text().strip())
                
                return True
        
            tr('td').each(parse_tds)
        
        return True
    
    data[child_name].append([])
    table_s0('tbody > tr').each(parse_s0_data)
    
    
    # Parse third table with id s1
    s1_data_header = ['Nr',
                      'Nazwa jednostki',
                      'Liczba uprawnionych do głosowania',
                      'Liczba kart wydanych',
                      'Liczba głosów oddanych',
                      'Liczba głosów ważnych',
                      'Liczba: kart wydanych / uprawnionych [%]']
    
    def parse_s1_data(i, element):
        nonlocal s1_data_header, data, child_name
        
        tr = pq(element)
        
        if tr('a').length == 1:
            data[child_name][2].append({})
            
            def parse_tds(i1, element1):
                nonlocal s1_data_header, data, child_name, i
                
                tr = pq(element1)
                
                if i1 > 6:
                    return False
                    
                data[child_name][2][-1][s1_data_header[i1]] = \
                    convertToProperType(tr('td:nth-child({})'.format(i1+1)).text().strip())
                
                if i1 == 1:
                    href = tr('td:nth-child({}) > a'.format(i1+1)).attr('href')
                    print('Processing {}...'.format(href))
                    
                    data[child_name][2][-1]['Child'] = {}
                    enumerateChild(pq(getFileFromURL(TEMPLATE_PAGE_URL.format(href))), data[child_name][2][-1]['Child'])
                
                return True
                
            tr('td').each(parse_tds)
            
        return True
        
    data[child_name].append([])
    table_s1('tbody > tr').each(parse_s1_data)
    
    return data
    

def main():
    root_pq = pq(getFileFromURL(TEMPLATE_PAGE_URL.format('index.htm')))
    
    data = enumerateChild(root_pq)
    
    with open('dataset.json', 'w') as dataset_file:
        json.dump(data, dataset_file)
    
    
    
if __name__ == '__main__':
    main()