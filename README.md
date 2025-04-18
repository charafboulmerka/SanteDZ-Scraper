# 🕷️ SanteDZ Scraper

A Python Scrapy project to extract detailed information about healthcare professionals (Médecins, Pharmacies, etc.) from the [sante-dz.com](https://www.sante-dz.com) website.

The scraped data can be exported to a **CSV file** or inserted directly into a **local MySQL database** using **phpMyAdmin (XAMPP)** or to an online database.

---

## 🌍 Overview

**SanteDZ Scraper** crawls the Sante-DZ directory and collects client information, including:

- 👤 Full Name  
- 🏥 Speciality or Profession  
- 📍 Address, City, and Wilaya  
- 📞 Phone Number(s)  
- 📧 Email (if available)  
- 🔗 Profile URL  
- 🌐 Other public info  

---

## ⚙️ Tech Stack

- Python 3.x  
- Scrapy (for crawling)  
- CSV module (optional export)  
- MySQL (with phpMyAdmin via XAMPP)  
- `mysql-connector-python` or `pymysql` (for DB connection)  

---
