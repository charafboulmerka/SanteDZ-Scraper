import scrapy
from scrapy_selenium import SeleniumRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import json
from bs4 import BeautifulSoup
from requests_html import HTMLSession
import requests
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
         yield SeleniumRequest(url=url, callback=self.parse,screenshot=True, wait_time=10,wait_until=EC.element_to_be_clickable((By.CLASS_NAME, 'btn-primary')))


  

    def parse(self, response):
        divs = response.css('div.links__contact')

            
        soup = BeautifulSoup(response.text, 'lxml')
        
        #get all divs with class "row -pas"
        all = soup.findAll('div',attrs={'class':"links__contact"})
        

        for(doctor) in all:
            header = doctor.find('a')
            #get previous p tag
            client_type = header.find_previous('p').text
            profile_link = f"https://annumed.sante-dz.com{header.get('href')}"
            yield scrapy.Request(profile_link,callback=self.getProfileData,meta={'client_type':client_type})

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
      


