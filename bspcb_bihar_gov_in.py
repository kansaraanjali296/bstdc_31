import os
import sqlite3
import warnings
import requests
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
import logging
import pyodbc
import re
from zipfile import ZipFile
from webdriver_manager.chrome import ChromeDriverManager

warnings.simplefilter("ignore")
driver = webdriver.Chrome(ChromeDriverManager().install())


# def RemoveExtraSpace(Content):
#     new = re.sub(' +', ' ', Content)
#     return new


def generate_file_name(url):
    # ----------------------------------------------url get file_name --------------------------------------------#
    file_name = url.split('://')[1].split("/")[0].replace(".", "_")
    return file_name


def download_file_dir(url):
    files_dir = os.path.expanduser('~') + "\\Documents\\" + "PythonFile\\" + url.split('://')[1].split("/")[0] + "_tender_py\\" + "File"
    if os.path.exists(files_dir):
        pass
    else:
        os.makedirs(files_dir)

    return files_dir


def log_file_dir():

    log_file_path = os.path.expanduser('~') + "\\Documents\\" + "PythonLog\\"
    if os.path.exists(log_file_path):
        pass
    else:
        os.makedirs(log_file_path)

    return log_file_path
    

def create_db(file_name, create_db_and_table_name):
    # ----------------------------------------------database created using sqlite ---------------------------------#
    conn = sqlite3.connect(file_name + '.db')
    cursor = conn.cursor()

    cursor.execute("CREATE TABLE IF NOT EXISTS " + create_db_and_table_name + "(Id INTEGER PRIMARY KEY, Tender_Notice_No TEXT, Tender_Summery TEXT, Tender_Details TEXT, Bid_deadline_2 TEXT, Documents_2 TEXT, TenderListing_key TEXT, Notice_Type TEXT, Competition TEXT, Purchaser_Name TEXT, Pur_Add TEXT, Pur_State TEXT, Pur_City TEXT, Pur_Country TEXT, Pur_Email TEXT, Pur_URL TEXT, Bid_Deadline_1 TEXT, Financier_Name TEXT, CPV TEXT, scannedImage TEXT, Documents_1 TEXT, Documents_3 TEXT, Documents_4 TEXT, Documents_5 TEXT, currency TEXT, actualvalue TEXT, TenderFor TEXT, TenderType TEXT, SiteName TEXT, createdOn TEXT, updateOn TEXT, Content TEXT, Content1 TEXT, Content2 TEXT, Content3 TEXT, DocFees TEXT, EMD TEXT, OpeningDate TEXT, Tender_No TEXT, Flag TEXT)")
    return conn


def download_pdf(links):
    # ***************** one by one File Download of any extension *****************
    all_links = links.split(',')
    if len(all_links) > 1:
        fullname = os.path.join(files_dir, datetime.now().strftime(f"%d%m%Y_%H%M%S%f") + '.zip')
        zip_obj = ZipFile(fullname, 'w')

        for pdfLink in all_links:
            filename = datetime.now().strftime(f"%d%m%Y_%H%M%S%f") + "." + pdfLink.rsplit('.', 1)[-1]
            response = requests.get(pdfLink)

            pdf = open(filename, 'wb')
            pdf.write(response.content)
            pdf.close()

            zip_obj.write(filename)
            os.remove(filename)
            logging.info("Zip File Downloaded")

    else:
        response = requests.get(links)
        fullname = os.path.join(files_dir, datetime.now().strftime(f"%d%m%Y_%H%M%S%f") + "." + links.rsplit('.', 1)[-1])

        pdf = open(fullname, 'wb')
        pdf.write(response.content)
        pdf.close()
        logging.info("File Downloaded")

    return fullname


def sqlite_and_sql_server_db(Page_Data, create_db_and_table_name):
    try:
        # ----------------------------------------------insert data in sqlite table ----------------------------------#
        que = "INSERT INTO " + create_db_and_table_name + " (Tender_Summery, Documents_2, Flag) VALUES (?, ?, 1)"
        conn.executemany(que, Page_Data)
        conn.commit()
        logging.info('SQLite Data Inserted')

        # ----------------------------------------------select sqlite data for insert in sql server -------------------
        sqlite_rows = conn.execute(
            "SELECT Tender_Summery, Documents_2, FROM " + create_db_and_table_name + " WHERE Flag = 1").fetchall()
        if len(sqlite_rows) > 0:
            sql_conn = pyodbc.connect('Driver={SQL Server};'
                                      'Server=192.168.100.153;'
                                      'Database=CrawlingDB;'
                                      'UID=anjali;'
                                      'PWD=anjali@123;')
            sql_cursor = sql_conn.cursor()
            sql_cursor.execute("IF NOT EXISTS (SELECT name FROM sysobjects WHERE name= '" + create_db_and_table_name + "' AND xtype='U') CREATE TABLE " + create_db_and_table_name + " (id int IDENTITY(1,1) PRIMARY KEY, Tender_Notice_No TEXT, Tender_Summery TEXT, Tender_Details TEXT, Bid_deadline_2 TEXT, Documents_2 TEXT, TenderListing_key TEXT, Notice_Type TEXT, Competition TEXT, Purchaser_Name TEXT, Pur_Add TEXT, Pur_State TEXT, Pur_City TEXT, Pur_Country TEXT, Pur_Email TEXT, Pur_URL TEXT, Bid_Deadline_1 TEXT, Financier_Name TEXT, CPV TEXT, scannedImage TEXT, Documents_1 TEXT, Documents_3 TEXT, Documents_4 TEXT, Documents_5 TEXT,currency TEXT, actualvalue TEXT, TenderFor TEXT, TenderType TEXT, SiteName TEXT, createdOn TEXT, updateOn TEXT, Content TEXT, Content1 TEXT, Content2 TEXT, Content3 TEXT, DocFees TEXT, EMD TEXT, OpeningDate TEXT, Tender_No TEXT)")

            # ----------------------------------------------insert data in sql server db -----------------------------#
            que1 = "INSERT INTO " + create_db_and_table_name + " (Tender_Summery, Documents_2) VALUES (?, ?)"
            sql_cursor.executemany(que1, sqlite_rows)
            sql_conn.commit()
            logging.info('SQL Server Data Inserted')
            sql_conn.close()

            # ----------------------------------------------update sqlite db for flag 1-------------------------------#
            conn.execute("UPDATE " + create_db_and_table_name + " SET Flag = 0 WHERE Flag = 1")
            conn.commit()

    except Exception as e:
        print(e)


# try:

url = 'http://bspcb.bihar.gov.in/tenders-notice.html'
driver.get(url)

create_db_and_table_name = url.split('://')[1].split("/")[0].replace(".", "_") + '_py'

file_name = generate_file_name(url)
conn = create_db(file_name, create_db_and_table_name)

log_file_path = log_file_dir()

logging.basicConfig(filename=log_file_path + file_name + ".log", filemode='a', level=logging.DEBUG, format='%(asctime)s %(message)s')
logging.info('Started Web Scraping')
logging.info('Program Start')

files_dir = download_file_dir(url)

tr_all_data = driver.find_elements(By.XPATH, value='//tbody//tr//*[@class="tblbg1"]')
Page_Data = []
print(Page_Data)


for tr_data in tr_all_data:

    if not 'Corrigendum' in tr_data.text:

        # Content = tr_data.get_attribute('innerHTML')
        # Content = RemoveExtraSpace(Content)
        # print(Content)

        sr_no = tr_data.find_element(By.XPATH, value='./td[1]').text.strip()
        print(sr_no)

        Tender_Summery = tr_data.find_element(By.XPATH, value='./td[2]').text.split('\n\n')[0].strip()
        print(Tender_Summery)

        links = []
        links_data = tr_data.find_elements(By.TAG_NAME, value='a')
        for lnk in links_data:
            if not 'Click To Visit E-tender' in lnk.text:
                lnk = lnk.get_attribute('href')
                links.append(lnk)
        links = ', '.join(links)
        print(links) 

        row_exists = "SELECT * FROM " + create_db_and_table_name + " WHERE Tender_Summery='" + Tender_Summery + "'"
        if not conn.execute(row_exists).fetchone():
            logging.info("Fresh")

            try:
                Documents_2 = download_pdf(links)
                print(Documents_2)
            except:
                Documents_2 = ''
            # Documents_2 = fullname

            Row_data = [Tender_Summery, Documents_2]
            Page_Data.append(Row_data)

        else:
            print("This Tender_Summery is already exist.")
            logging.info("Duplicated")

        print("--------------------------------------")

sqlite_and_sql_server_db(Page_Data, create_db_and_table_name)

conn.close()
driver.close()
logging.info('Proceed Successfully Done')
print("Completed")


# except Exception as e:
#     print(e)