import pandas as pd #imports certain files (franklin) and cleans files in stitcher object
from ohiodistricts import countyCodes #imports list of ohio counties
from urllib.request import Request, urlopen #allows opening of files through http: protocol without a browser object
from selenium import webdriver #creates the browser onbject
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support.ui import Select
from selenium.webdriver import FirefoxProfile
from selenium.webdriver import Firefox
import datetime #needed to create time stamped libraries
import time # needed to get the program to wait long enough to download files
import os #needed to navigate through path environment
from stitcher import Stitcher #imports stitcher object that writes the files into a single uploadable file

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
        #even though the same election name is being repeated 4 times here, the list is necessary for primary election versions of this program. 
        self.election_name = ['20200317P', '20200317P', '20200317P', '20200317P']
        fpath = os.getcwd()
        fpath = fpath+'/output/'
        today = datetime.datetime.today()
        date = (str(today.month), str(today.day), str(today.year), str(today.hour), str(today.minute))
        date = '-'.join(date)
        newdir = fpath+date+'/'
        os.mkdir(newdir)
        self.fpath = newdir

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

    def fail(self, county, message):
        print('{} failed {}'.format(county, message))
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
        fpath = self.fpath
        df.to_csv(fpath+'failed_counties.csv', index = False) 
    def urls(self, county):
        '''This function could probably do more, but meh.'''
        data_url = '''https://lookup.boe.ohio.gov/vtrapp/{}/avreport.aspx'''.format(county.lower())
        if county == 'Van Wert': #because van wert has to be special.
            data_url = 'https://lookup.boe.ohio.gov/vtrapp/vanwert/avreport.aspx'
        return data_url
    def write(self, name='fullfile.csv'):
        stitch = Stitcher(self.fpath)
        files = len(self.successful)-1
        try:
            stitch.import_vf(files)
        except:
            print("VF files failed")
        try:
            stitch.import_franklin()
        except:
            print("Whoops, no franklin.")
        try:
            stitch.import_hamilton()
        except Exception as e:
            print("whoops, no Hamilton: {}".format(e))
        stitch.write(fname = name) 
    @property
    def counties(self):
        return self.__attempt_counties
    def default_steps(self,browser, data_url, delay):
        browser.get(data_url)
        select_element = Select(browser.find_element_by_id('cmbelectionlist'))
        #I really hate these try/except blocks, but they fucking work.
        #There are three possible options. selenium throws an error if you ask it to select something that's not there.
        
        try:
            select_element.select_by_value(self.election_name[0])
        except:
            try:
                select_element.select_by_value(self.election_name[1])
            except:
                select_element.select_by_value(self.election_name[2])
        browser.find_element_by_id('rdo_file').click()
        browser.find_element_by_id('btnStart').click()
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)
        try:
            print('Attempting to download')
            browser.find_element_by_id('btn_download').click()
        except:
            print('First attempt failed. Waiting 4 seconds, then trying again.')
            time.sleep(delay)
            browser.find_element_by_id('btn_download').click()
    
    def athens_steps(self,browser, data_url):
        '''This is legacy code and could probably simply just be eliminated.
        
        I have not eliminated it because I am afraid of unintentionally breaking something else. '''
        browser.get(data_url)
        select_element = Select(browser.find_element_by_id('cmbelectionlist'))
        select_element.select_by_value(self.election_name[0])
        browser.find_element_by_id('rdo_file').click()
        browser.find_element_by_id('btnStart').click()
        time.sleep(3)
        browser.find_element_by_id('btn_download').click()
    
    def carroll_steps(self,browser,data_url, delay):
        '''There are a few counties that make sort by date a default option when you select the desired election.

        For these counties, the carroll_steps are required.
        '''
        browser.get(data_url)
        print('finding election name')
        select_element = Select(browser.find_element_by_id('cmbelectionlist'))
        try:
            print('Try 1')
            select_element.select_by_value(self.election_name[1])
        except Exception as emmie:
            try:
                print("Got the following exception message: "+str(emmie))
                print('Try two... clearing election selection, then trying again')
                select_element.select_by_value('NONE')
                print('Clicking again')
                select_element.select_by_value('20200317P')
            except:
                try:
                    print('Clicking a third time')
                    select_element.select_by_value(self.election_name[0])
                except: 
                    print('Fuck it. Gonna try without clicking a date')
        print('setting radio to no date')
        browser.find_element_by_id('rdo_dtno').click()
        print('Setting radio to downloadable file')
        browser.find_element_by_id('rdo_file').click()
        time.sleep(3)
        try:
            print("Attempting to hit start")
            browser.find_element_by_id('btnStart').click()
        except:
            try:
                time.sleep(delay)
                browser.find_element_by_id('rdo_dtno').click()
                browser.find_element_by_id('btnStart').click()
            except Exception as e:
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                browser.find_element_by_id('btnStart').click()
                print(str(e))
        time.sleep(delay)
        try:
            browser.find_element_by_id('btn_download').click()
        except:
            
            browser.find_element_by_id('btn_download').click()

    def retrieve_votefind(self, browser, delay = 4):
        '''This program would probably work a little better if the browser was passed to votefind, and votefind used the browser to call links.
        
        However, that's now how I wrote this fucker. This function retrieves the URL from votefind, then passes the url and the desired delay to the steps. 
        
        If the county is in a set of Carroll, Geauga, Guernsey, Montgomery, or Morgan, they have special steps. 
        
        Otherwise, the default steps go to work.
        
        votefind.failed_counties() is also called in this function'''
        for county in self.counties:
            print("Attempting {}".format(county))
            data_url = self.urls(county)
            try:
                if county in ('Carroll','Geauga', 'Guernsey', "Montgomery", "Morgan"):
                    self.carroll_steps(browser, data_url, delay)
                else:
                    self.default_steps(browser, data_url, delay)
                self.success(county)
                print('Wrote {}'.format(county))
            except Exception as em:
                self.fail(county, str(em)) #this exception block allows the program to keep working if a county fails
        self.failed_counties()


class Browser(Firefox):
    '''This is an instance of the selenium firefox browser set with a custom profile that allows me to save my files where I want.
    
    It also carries out the steps for accessing and saving county early vote data.'''
    def __init__(self, npath):
        
        
        fpath = os.getcwd()
        
        #This is a little hacky, but it makes the code compatible with both linux and windows.
        if '\\' in fpath:
            ffpath = npath.replace('/', '\\')
        else:
            ffpath = npath
        
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
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'txt'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'TXT file'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'CSV file'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'hidden'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "'Text Document'")
        ffprofile.set_preference("browser.helperAdds.neverAsk.saveToDisk", "Text Document")
        
        preferences = ffprofile.default_preferences
        print('Browser preferences set...')
        print('Loading browser....')
        super().__init__(firefox_profile=ffprofile,  executable_path="geckodriver.exe" )
        print("Browser loaded. Let's do this!")
        
    
    

     
class Other_Counties(object):
    def __init__(self, fpath):
        counties = ['Ashland', 'Butler', 'Clermont','Crawford',"Cuyahoga", "Fairfield", 'Fayette', 'Franklin', 'Hamilton', 'Hancock', 'Henry', 'Huron','Medina', 'Mercer',
        'Ottawa', 'Richland', 'Sandusky', 'Shelby', 'Stark', 'Summit', 'Trumbull', 'Wayne', 'Wood', 'Wyandot']
        self.counties = counties
        self. attempt_counties = ['Cuyahoga', 'Franklin']
        self.fpath = fpath 
    def retrieve_franklin(self,browser, fpath = 'O:/Python Scripts/ev scraper/output/', fname = 'franklin.csv'):
        franklin_columns = ['BALLOT PARTY', 'DATE REQUESTED', 'DATE MAILED', 'DATE RETURNED']
        franklin_corrected = ['PARTYAFFIL', 'AVAPPDATE', 'AVSENTDATE', 'AVRECVDATE']
        df =pd.read_csv('http://boelcd.franklincountyohio.gov/assets/components/ftp.cfc?method=getOverSFTP&LocalPathName=F%3A%5C%5CBOEL%5C%5Cpublic%5C%5Cdownloads%5C%5C&RemotePathName=%2Fpublic%2Fdownloads%2F&FileName=ABSENTEE_LABELS_NEW.txt&Overwrite=true&Delete=true', index_col = 24, delimiter = '\t', low_memory = 'False')
        df = df[franklin_columns]
        df.columns = franklin_corrected
        df.index.names = ['sos_id']
        npath = os.getcwd()
        df.to_csv(self.fpath+fname)
    def retrieve_franklin2(self, browser, fpath = 'O:/Python Scripts/ev scraper/output/', fname = 'franklin.csv'):
        browser.get('https://vote.franklincountyohio.gov/Maps-Data/Absentee-Voter-Labels')
        select_element = Select(browser.find_element_by_id('p_lt_ctl08_pageplaceholder_p_lt_ctl01_AbsenteeVoterLabels_electionDropdown'))
        #I really hate these try/except blocks, but they fucking work.
        #There are three possible options. selenium throws an error if you ask it to select something that's not there.
        
        
        select_element.select_by_value('413')

        select_element2 = Select(browser.find_element_by_id('p_lt_ctl08_pageplaceholder_p_lt_ctl01_AbsenteeVoterLabels_districtTypeDropdown'))
        select_element2.select_by_value('25')
        time.sleep(3)
        select_element3 = Select(browser.find_element_by_id('p_lt_ctl08_pageplaceholder_p_lt_ctl01_AbsenteeVoterLabels_districtDropdown'))
        select_element3.select_by_value('1079')
        time.sleep(3)
        browser.find_element_by_id('p_lt_ctl08_pageplaceholder_p_lt_ctl01_AbsenteeVoterLabels_exportText').click()
    def retrieve_cuyahoga(self,browser):
        print("Finding Cuyahoga")
        browser.get('https://boe.cuyahogacounty.us/en-US/absentee-voter-labels.aspx')
        
        select_element = Select(browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_ddlElection_Date'))
        #Cuyahoga county orders election dates sequentially. 212 corresponds to the November 5 General election. Unless there is a special, then 213 would be the March primary
        select_element.select_by_value('227')

        change_date = browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_txtDateIssuedFrom')
        change_date.clear()
        change_date.send_keys('1/1/2020')

        change_other_date = browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_txtDateIssuedTo')
        change_other_date.clear()
        change_other_date.send_keys('6/2/2020')

        select_race = Select(browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_ddlDistrictTypes'))
        select_race.select_by_value('ALL')

        time.sleep(3)

        select_nested = Select(browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_ddlDistrict'))
        select_nested.select_by_value('2')

        print("Downloading Cuyahoga")

        time.sleep(1)

        browser.find_element_by_id('ContentPlaceHolder1_ContentPlaceHolderMain_btnExport').click()
        print("Cuyahoga Written")

    def retrieve_hamilton(self, browser):
        print("Finding Hamilton")
        browser.get('https://boe.hamilton-co.org/data/absentee-voters-list.aspx')

        #browser.execute_script("window.scrollTo(500, document.body.scrollHeight);")

        #change_date = browser.find_element_by_id('applicationStartDate')
        #change_date.send_keys('1/1/2020')

        #change_other_date = browser.find_element_by_id('applicationEndDate')
        #change_other_date.send_keys('3/17/2020')
        time.sleep(4)

        dl_button = browser.find_elements_by_css_selector(".btn.primary")
        button_counter = 0
        for f in dl_button:
            button_counter +=1
            if button_counter == 1:
                pass
            else:
                f.click()      

    def retrieve_stark(self,browser):
        print('Finding Stark')
        browser.get('https://www.starkcountyohio.gov/cmspages/logon.aspx?returnurl=%2fboard-of-elections%2fcandidates-issues-information%2fabsentee-download%3fext%3d.')
        time.sleep(4)
        browser.find_element_by_id('Login1_lblUserName').send_keys('candidate')

        browser.find_element_by_id('Login1_lblPassword').send_keys('avlabels')

def retrieve_html(url = 'htts://allen.ohioboe.com/apps/finished.aspx'):
    '''100% legacy code, but this is useful for troubleshooting.'''
    from bs4 import BeautifulSoup
    myHeaders = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36', 'Referer': 'https://www.nseindia.com', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'}
    url_request  = Request(url, headers=myHeaders)
    html = urlopen(url_request ).read()
    soup = BeautifulSoup(html)
    return soup, html


def main(): 
    
    votefind = Votefind() #creates the votefind object for votefind counties.
    
    browser = Browser(votefind.fpath) #initializes the brwoser

    votefind.retrieve_votefind(browser)
    votefind.retrieve_votefind(browser, 8)

    

    not_votefind = Other_Counties(votefind.fpath)
    try:
        not_votefind.retrieve_cuyahoga(browser)
    except:
        print("Cuyahoga failed")
    try:
        not_votefind.retrieve_franklin(browser)
    except Exception as e:
        print("Franklin Failed. Whatever. Fuck franklin. Reason: {}".format(e))
    try:
        not_votefind.retrieve_hamilton(browser)
    except:
        print("Hamilton might have failed. Who knows. Hamilton is screwy.")
    time.sleep(60)
    browser.close() #ends the browser sesison.
    

    votefind.write() #writes the full file
    print("File written successfully.")

def main2():
    '''Testing out Hamilton county on its own since hamilton county changed up their website to using CSS buttons instead of Javascript buttons'''
    votefind = Votefind() #creates the votefind object for votefind counties.
    
    browser = Browser(votefind.fpath) #initializes the brwoser
    not_votefind = Other_Counties(votefind.fpath)
    not_votefind.retrieve_franklin(browser)


    

#main
main()
#main2()