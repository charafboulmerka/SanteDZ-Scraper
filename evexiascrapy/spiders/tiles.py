import scrapy
# from scrapy_selenium import SeleniumRequest
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support import expected_conditions as EC
import json
from bs4 import BeautifulSoup
import urllib.parse as p
import re
import mysql.connector
import html


class TilesSpider(scrapy.Spider):
    name = 'clients'
    allowed_domains = ['annumed.sante-dz.com']

    def __init__(self, *args, **kwargs):  
        self.mydb = mysql.connector.connect(user='root', password='',
                              host='127.0.0.1',
                              database='infy_projects')
        # create infy_projects database if not exists
        self.mycursor = self.mydb.cursor()
        self.mycursor.execute("CREATE DATABASE IF NOT EXISTS infy_projects")
        self.mycursor.execute("USE infy_projects")

        self.mCount = 0                   

    def start_requests(self):
        for page in range(1,2681):
            url = f"https://annumed.sante-dz.com/annuaire/filter?term=&wilaya=&commune=&categorie=medecin&speciality=&distance=&page={page}"
            yield scrapy.Request(url=url, callback=self.parse)
        #  yield SeleniumRequest(url=url, callback=self.parse,screenshot=True, wait_time=10,wait_until=EC.element_to_be_clickable((By.CLASS_NAME, 'btn-primary')))


    
  

    def parse(self, response):
        divs = response.css('div.links__contact')

            
        soup = BeautifulSoup(response.text, 'lxml')
        
        #get all divs with class "row -pas"
        all = soup.findAll('div',attrs={'class':"links__contact"})
        

        # for(doctor) in all:
        #     header = doctor.find('a')
        #     #get previous p tag
        #     client_type = header.find_previous('p').text
        #     profile_link = f"https://annumed.sante-dz.com{header.get('href')}"
        #     # yield scrapy.Request(profile_link,callback=self.getProfileData,meta={'client_type':client_type})
        #     yield scrapy.Request(profile_link, callback=self.get_rockikz_profile_data, cookies=response.request.cookies)
        profile_links = self.get_profile_links(response)
        for profile_link in profile_links:
            yield scrapy.Request(p.urljoin("https://annumed.sante-dz.com", profile_link), callback=self.get_rockikz_profile_data, cookies=response.request.cookies)

    def get_profile_links(self, response):
        # <a itemprop="url" href="/detail/medecin/noureddine-elagag?ref=intern-page">
        #     <h3 itemprop="name">Noureddine Elagag</h3>
        # </a>
        profile_links = []
        urls = response.css('a[itemprop="url"]::attr(href)').getall()
        for url in urls:
            if self.is_already_in_db(url):
                print(f"[***] Already in db: {url}")
                continue
            profile_links.append(url)
        return profile_links
                
                
    def is_already_in_db(self, url):
        # self.mycursor.execute("SELECT * FROM clients WHERE url = %s", (url,))
        # myresult = self.mycursor.fetchall()
        # return myresult
        return False
            
        
    

    def getWilayaIndex(self,wilaya_name):
        wilaya = ["Adrar","Chlef","Laghouat","Oum El Bouaghi","Batna","Béjaïa","Biskra","Béchar","Blida"
        ,"Bouira","Tamanrasset","Tébessa","Tlemcen","Tiaret","Tizi Ouzou","Alger","Djelfa","Jijel","Sétif","Saïda"
        ,"Skikda","Sidi Bel Abbès","Annaba","Guelma","Constantine","Médéa","Mostaganem"
        ,"M'Sila","Mascara","Ouargla","Oran","El Bayadh","Illizi","Bordj Bou Arréridj"
        ,"Boumerdès","El Tarf","Tindouf","Tissemsilt","El Oued","Khenchela","Souk Ahras"
        ,"Tipaza","Mila","Aïn Defla","Naâma","Aïn Témouchent","Ghardaïa","Relizane"]
        for index, w in enumerate(wilaya):
            if w == wilaya_name:
                return index+1
        return -1  

    def get_rockikz_profile_data(self, response):
        api_url = "https://annumed.sante-dz.com/api/v1/phone"
        # get the csrf token in the response <input type="hidden" name="_token" value="...">
        x_csrf_token = response.css('input[name="_token"]::attr(value)').get()
        # get the data entity & place
        # data_entity = soup.find("a", attrs={"itemprop": "telephone"}).attrs.get("data-entity")
        # data_place = soup.find("a", attrs={"itemprop": "telephone"}).attrs.get("data-place")
        data_entity = response.css('a[itemprop="telephone"]::attr(data-entity)').get()
        data_place = response.css('a[itemprop="telephone"]::attr(data-place)').get()
        # print variable name & value
        print(f"{x_csrf_token=}")
        print(f"{data_entity=}")
        print(f"{data_place=}")
        cookie = response.headers.getlist('Set-Cookie')[0].decode().split(';')
        # convert the cookie to a dict
        cookie = {c.strip().split('=')[0]: c.strip().split('=')[1] for c in cookie}
        if data_entity and data_place:
            # get the remaining data here, tags & cordinates (lat & long)
            # <span class="tag speciliate">Gyn&eacute;co-Obstetrique</span></a>
            # tags = soup.findAll('a',attrs={'title':"Filter par cette spétialité"})
            tags = response.css('a[title="Filter par cette spétialité"]')
            # convert to a list of tag texts
            tags = [tag.css('span::text').get().strip() for tag in tags]
            # convert to a string
            tags = '|'.join(tags)
            # <meta itemprop="latitude" content="36.485007" />
            # <meta itemprop="longitude" content="2.838839" />
            # get the latitude & longitude
            latitude = response.css('meta[itemprop="latitude"]::attr(content)').get()
            longitude = response.css('meta[itemprop="longitude"]::attr(content)').get()
            # make a post request instead
            yield scrapy.FormRequest(
                api_url, method="POST", 
                formdata={"entity": data_entity, "id": data_place}, 
                meta={"tags": tags, "latitude": latitude, "longitude": longitude},
                headers={
                    "pt": "text/html, */*; q=0.01",
                    "accept-encoding": "gzip, deflate, br",
                    "accept-language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7,ar;q=0.6",
                    "cache-control": "no-cache",
                    "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "origin": "https://annumed.sante-dz.com",
                    "pragma": "no-cache",
                    "referer": response.url,
                    "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
                    "sec-ch-ua-mobile": "?0",
                    "sec-ch-ua-platform": "Windows",
                    "sec-fetch-dest": "empty",
                    "sec-fetch-mode": "cors",
                    "sec-fetch-site": "same-origin",
                    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
                    "x-csrf-token": x_csrf_token,
                    "x-requested-with": "XMLHttpRequest",
                },
                cookies=cookie,
                callback=self.parse_rockikz_profile_data)
        else:
            # charaf's code
            print("===============Executing charaf's code================")
            soup = BeautifulSoup(response.text, 'lxml')
            script = soup.find('script', type='application/ld+json').text
            #script replace div with span
            script = script.replace('<div class="quota__exceeded--info">L\'adresse est désactivé <span class="tool-tip more-info" title="L\'adresse est désactivé">plus d\'info</span></div>','')
            #regex script
            script = re.sub(r'[\t\n\r]', '', script)
            
            json_data = json.loads(script)

            name = json_data['name']
            address = html.unescape(json_data['address']['streetAddress'])
            wilaya_txt = html.unescape(json_data['address']['addressRegion'])
            wilaya_id = self.getWilayaIndex(wilaya_txt)
            commune_txt = html.unescape(json_data['address']['addressLocality'])
            code_postal = json_data['address']['postalCode']

            latitude = json_data['geo']['latitude']
            longitude = json_data['geo']['longitude']
            allTags = soup.findAll('a',attrs={'title':"Filter par cette spétialité"})
            #get spans from all a tags
            spans = []
            allTagsTxt = ''
            for tag in allTags:
                spans.append(tag.find('span').text)
                #add all spans to txt
                allTagsTxt += tag.find('span').text+"|"
            allTagsTxt = allTagsTxt[:-1]
            yield {
                'id':self.mCount,'name': name, 'address': address,
                'wilaya_txt':wilaya_txt,'commune_txt':commune_txt,
                'code_postal':code_postal, 'latitude': latitude, 
                'longitude': longitude,',allTagsTxt':allTagsTxt,'link': response.request.url
            }  
            self.mCount += 1
        
        
        
    def parse_rockikz_profile_data(self, response):
        # get the name of the doctor, <h3 class="name" itemprop="name">BAKA MENNOUBA</h3>
        name = response.css('h3.name::text').get().strip()
        # street addresss <div itemprop="streetAddress">24 rue kriti mokhtar</div>
        street_address = response.css('div[itemprop="streetAddress"]::text').get().strip()
        # address locality <div itemprop="addressLocality"><a href="/filter/commune/287">Blida</a>, <ahref="/filter/wilaya/9">Blida</a></div>
        # get the commune & wilaya
        anchors = response.css('div[itemprop="addressLocality"] a')
        commune = anchors[0].css('::text').get().strip()
        wilaya = anchors[1].css('::text').get().strip()
        # get the phone number <h3 class="phone-number"> <a href="tel:+213 25 32 19 78" title="Appelle-le maintenant" itemprop="telephone">+213 25 32 19 78</a> </h3>
        phone_number = response.css('h3.phone-number a::text').get().replace(" ", "") # removing the spaces in the phone number
        yield {
            "name": name,
            "street_address": street_address,
            "commune": commune,
            "wilaya": wilaya,
            "tags": response.meta.get("tags"),
            "latitude": response.meta.get("latitude"),
            "longitude": response.meta.get("longitude"),
            "phone_number": phone_number,
        }

        
    def getProfileData(self, response):
        department_id = 0
        client_type = response.meta['client_type']

        if(client_type == "Pharmacie" or client_type == "pharmacie"):
            department_id = 2
        else:
            department_id = 3

        soup = BeautifulSoup(response.text, 'lxml')
        script = soup.find('script', type='application/ld+json').text
        #script replace div with span
        script = script.replace('<div class="quota__exceeded--info">L\'adresse est désactivé <span class="tool-tip more-info" title="L\'adresse est désactivé">plus d\'info</span></div>','')
        #regex script
        script = re.sub(r'[\t\n\r]', '', script)
        
        json_data = json.loads(script)

        name = json_data['name']
        address = html.unescape(json_data['address']['streetAddress'])
        wilaya_txt = html.unescape(json_data['address']['addressRegion'])
        wilaya_id = self.getWilayaIndex(wilaya_txt)
        commune_txt = html.unescape(json_data['address']['addressLocality'])
        code_postal = json_data['address']['postalCode']

        latitude = json_data['geo']['latitude']
        longitude = json_data['geo']['longitude']
        allTags = soup.findAll('a',attrs={'title':"Filter par cette spétialité"})
    #get spans from all a tags
        spans = []
        allTagsTxt = ''
        for tag in allTags:
            spans.append(tag.find('span').text)
            #add all spans to txt
            allTagsTxt += tag.find('span').text+"|"
        allTagsTxt = allTagsTxt[:-1]

        yield {'id':self.mCount,'name': name, 'address': address,'wilaya_txt':wilaya_txt,'commune_txt':commune_txt,
        'code_postal':code_postal, 'latitude': latitude, 'longitude': longitude,',allTagsTxt':allTagsTxt,'link': response.request.url}  
        mycursor = self.mydb.cursor()
        sql = "INSERT INTO clients (name, address,wilaya_id,wilaya_txt,commune_txt,code_postal,tags_txt,type_txt,longitude, latitude, department_id,created_by,created_at,updated_at ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        sql_created_at = "2022-11-15 13:54:14"
        val = (name,address,wilaya_id,wilaya_txt,commune_txt,code_postal,allTagsTxt,client_type,longitude,latitude,department_id,1,sql_created_at,sql_created_at)

        mycursor.execute(sql, val)
        self.mydb.commit()
        self.mCount=self.mCount+1
        print(mycursor.rowcount, "record inserted.")
        print(self.mCount,name,address,latitude,longitude)
      


