import pandas as pd 
from ohiodistricts import countyCodes
from urllib.request import Request, urlopen
from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import Select
from bs4 import BeautifulSoup
from selenium.webdriver import FirefoxProfile
from selenium.webdriver import Firefox
import time
import os
from stitcher import Stitcher

class Votefind(object):
    '''The votefind object stores the successful and unsuccessful counties.
    It also supplies the list of counties to attempt in a first and second round. 
    It also supplies the list of successful and unsuccessful counties 
    
    Future versions could include the proper steps for the browser.'''
    def __init__(self):
        self.build_counties()
        self.successful = []
        self.failed = []
        self.attempts = 0

    def build_counties(self):
        print('Populating county list')
        fpath = os.getcwd()
        df = pd.read_csv(fpath+'/input/votefind_urls.csv')
        county_df = df['county']
        self.__counties = []
        for i in county_df:
            self.__counties.append(i)
        self.__attempt_counties = self.__counties
        print('County list built.')
    def success(self, county):
        self.successful.append(county)

    def fail(self, county):
        print('{} failed'.format(county))
        self.failed.append(county)
        if county in self.successful:
            self.successful.remove(county) #this block should basically never work. It exists because of a legacy version.

    def failed_counties(self):
        '''Creates a list of failed counties. Sets the order of attempts for a second run.'''
        self.attempts +=1
        print('The following counties failed:')
        if self.attempts <2: #Why should attempts ever be more than 2? It shouldn't. But the first version accidentally created an infinite loop. This prevents that.
            self.__attempt_counties = []
            for county in self.failed:
                print(county)
                self.__attempt_counties.append(county)
            self.failed = []
            print('Second attempt incoming.')
        else: 
            print('Out of attempts')
            self.__attempt_countes = []
            self.write_failed()
    def write_failed(self):
        failed_counties = {'failed':self.failed} #If I knew pandas better, I wouldn't have to do this. 

        df = pd.DataFrame(failed_counties) 
        fpath = os.getcwd()
        df.to_csv(fpath+'/output/failed_counties.csv', index = False) #in future version, os should detect current working directory
    def urls(self, county):
        '''This function could probably do more, but meh.'''
        data_url = '''https://{}.ohioboe.com/apps/avreport.aspx'''.format(county.lower())
        if county == 'Van Wert': #because van wert has to be special.
            data_url = 'https://vanwert.ohioboe.com/apps/avreport.aspx'
        return data_url
    def write(self, name='fullfile.csv'):
        stitch = Stitcher()
        files = len(self.successful)-1
        stitch.import_vf(files)
        stitch.import_franklin()
        stitch.import_hamilton()
        stitch.write(fname = name) 
    @property
    def counties(self):
        return self.__attempt_counties

class Browser(Firefox):
    '''This is an instance of the selenium firefox browser set with a custom profile that allows me to save my files where I want.
    
    It also carries out the steps for accessing and saving county early vote data.'''
    def __init__(self):
        
        
        fpath = os.getcwd()
        
        #This is a little hacky, but it makes the code compatible with both linux and windows.
        if '\\' in fpath:
            ffpath = fpath+ '\\output'
        else:
            ffpath = fpath+ '/output'
        
        print('Initializing browser....')
        ffprofile = FirefoxProfile(fpath+'/input')
        #ffprofile = FirefoxProfile()
        #ffprofile.set_preference("browser.download.folderList", 2)
        ffprofile.set_preference("browser.download.manager.showWhenStarting", False)
        ffprofile.set_preference("browser.helperApps.neverAsk.saveToDisk", '"application/xls"')
        ffprofile.set_preference("browser.download.dir",ffpath)
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'Microsoft Excel Comma Separated Values File'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'Excel'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'csv'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'CSV file'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'hidden'")
        preferences = ffprofile.default_preferences
        print('Browser preferences set...')
        print('Loading browser....')
        super().__init__(firefox_profile=ffprofile,  executable_path="geckodriver.exe" )
        print("Browser loaded. Let's do this!")
        self.election_name = ['20190507PS', '20190507S', '20190507P']
    
    
    def default_steps(self,data_url, delay):
        self.get(data_url)
        select_element = Select(self.find_element_by_id('cmbelectionlist'))
        #I really hate these try/except blocks, but they fucking work.
        #There are three possible options. selenium throws an error if you ask it to select something that's not there.
        
        try:
            select_element.select_by_value(self.election_name[0])
        except:
            try:
                select_element.select_by_value(self.election_name[1])
            except:
                select_element.select_by_value(self.election_name[2])
        self.find_element_by_id('rdo_file').click()
        self.find_element_by_id('btnStart').click()
        self.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)
        try:
            print('Attempting to download')
            self.find_element_by_id('btn_download').click()
        except:
            print('First attempt failed. Waiting 4 seconds, then trying again.')
            time.sleep(delay)
            self.find_element_by_id('btn_download').click()
    
    def athens_steps(self, data_url):
        '''This is legacy code and could probably simply just be eliminated.
        
        I have not eliminated it because I am afraid of unintentionally breaking something else. '''
        self.get(data_url)
        select_element = Select(self.find_element_by_id('cmbelectionlist'))
        select_element.select_by_value(self.election_name[0])
        self.find_element_by_id('rdo_file').click()
        self.find_element_by_id('btnStart').click()
        time.sleep(3)
        self.find_element_by_id('btn_download').click()
    
    def carroll_steps(self,data_url, delay):
        '''There are a few counties that make sort by date a default option when you select the desired election.

        For these counties, the carroll_steps are required.
        '''
        self.get(data_url)
        select_element = Select(self.find_element_by_id('cmbelectionlist'))
        try:
            select_element.select_by_value(self.election_name[1])
        except:
            try:
                select_element.select_by_value(self.election_name[2])
            except:
                    select_element.select_by_value(self.election_name[0])
        self.find_element_by_id('rdo_file').click()
        self.find_element_by_id('rdo_dtno').click()
        try: 
            self.find_element_by_id('btnStart').click()
        except:
            time.sleep(delay)
            self.find_element_by_id('rdo_dtno').click()
            self.find_element_by_id('btnStart').click()
        time.sleep(delay)
        self.find_element_by_id('btn_download').click()

    def retrieve_votefind(self, votefind, delay = 4):
        '''This program would probably work a little better if the browser was passed to votefind, and votefind used the browser to call links.
        
        However, that's now how I wrote this fucker. This function retrieves the URL from votefind, then passes the url and the desired delay to the steps. 
        
        If the county is in a set of Carroll, Geauga, Guernsey, Montgomery, or Morgan, they have special steps. 
        
        Otherwise, the default steps go to work.
        
        votefind.failed_counties() is also called in this function'''
        for county in votefind.counties:
            print("Attempting {}".format(county))
            data_url = votefind.urls(county)
            try:
                if county in ('Carroll','Geauga', 'Guernsey', "Montgomery", "Morgan"):
                    self.carroll_steps(data_url, delay)
                else:
                    self.default_steps(data_url, delay)
                votefind.success(county)
                print('Wrote {}'.format(county))
            except:
                votefind.fail(county) #this exception block allows the program to keep working if a county fails
        votefind.failed_counties()
     
class Other_Counties(object):
    def __init__(self):
        counties = ['Ashland', 'Butler', 'Clermont','Crawford',"Cuyahoga", "Fairfield", 'Fayette', 'Franklin', 'Hamilton', 'Hancock', 'Henry', 'Huron','Medina', 'Mercer',
        'Ottawa', 'Richland', 'Sandusky', 'Shelby', 'Stark', 'Summit', 'Trumbull', 'Wayne', 'Wood', 'Wyandot']
        self.counties = counties
        self. attempt_counties = ['Cuyahoga', 'Franklin'] 
    def retrieve_franklin(self, fpath = 'O:/Python Scripts/ev scraper/output/', fname = 'franklin.csv'):
        franklin_columns = ['SOS VOTER ID','PARTY OF BALLOT SELECTED', 'DATE REQUESTED', 'DATE MAILED', 'DATE RETURNED']
        franklin_corrected = ['SOSID','PARTYAFFIL','AVAPPDATE', 'AVSENTDATE', 'AVRECVDATE']
        df =pd.read_csv('http://boelcd.franklincountyohio.gov/assets/components/ftp.cfc?method=getOverSFTP&LocalPathName=F%3A%5C%5CBOEL%5C%5Cpublic%5C%5Cdownloads%5C%5C&RemotePathName=%2Fpublic%2Fdownloads%2F&FileName=ABSENTEE_LABELS_NEW.txt&Overwrite=true&Delete=true', delimiter = '\t')
        df = df[franklin_columns]
        df.columns = franklin_corrected
        npath = os.getcwd()
        df.to_csv(npath+'/output/'+fname, index=False)
    def retrieve_cuyahoga(self,browser):
        print("Finding Cuyahoga")
        browser.get('https://boe.cuyahogacounty.us/en-US/absentee-voter-labels.aspx')
        
        select_element = Select(browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_ddlElection_Date'))
        select_element.select_by_value('209')

        change_date = browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_txtDateIssuedFrom')
        change_date.clear()
        change_date.send_keys('1/1/2019')

        change_other_date = browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_txtDateIssuedTo')
        change_other_date.clear()
        change_other_date.send_keys('5/6/2019')

        select_race = Select(browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_ddlDistrictTypes'))
        select_race.select_by_value('ALL')

        time.sleep(1)

        select_nested = Select(browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_ddlDistrict'))
        select_nested.select_by_value('2')

        print("Downloading Cuyahoga")

        time.sleep(1)

        browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_btnExport').click()
        print("Cuyahoga Written")

    def retrieve_hamilton(self, browser):
        print("Finding Hamilton")
        browser.get('https://boe.hamilton-co.org/data/absentee-voters-list.aspx')

        

        change_date = browser.find_element_by_id('ContentMain_ContentMain_phMainContent_txtRequest1')
        change_date.clear()
        change_date.send_keys('1/1/2019')

        change_other_date = browser.find_element_by_id('ContentMain_ContentMain_phMainContent_txtRequest2')
        change_other_date.clear()
        change_other_date.send_keys('5/6/2019')

        browser.find_element_by_id('ContentMain_ContentMain_phMainContent_btncsv').click()


def retrieve_html(url = 'htts://allen.ohioboe.com/apps/finished.aspx'):
    '''100% legacy code, but this is useful for troubleshooting.'''
    myHeaders = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', 'Referer': 'https://www.nseindia.com', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    url_request  = Request(url, headers=myHeaders)
    html = urlopen(url_request ).read()
    soup = BeautifulSoup(html)
    return soup, html


def main(): 
    
    votefind = Votefind() #creates the votefind object for votefind counties.
    
    browser = Browser() #initializes the brwoser

    browser.retrieve_votefind(votefind) #retrieves votefind counties if possible
    #try 2
    browser.retrieve_votefind(votefind, 8) #repeats, with 8 second delay before the download step

    not_votefind = Other_Counties()
    not_votefind.retrieve_cuyahoga(browser)
    not_votefind.retrieve_hamilton(browser)
    not_votefind.retrieve_franklin()
    time.sleep(60)

    browser.close() #ends the browser sesison.
    

    votefind.write() #writes the full file

    

#main
main()
