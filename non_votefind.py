from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
import pandas as pd

class Other_Counties(object):
    def __init__(self):
        counties = ['Ashland', 'Butler', 'Clermont','Crawford',"Cuyahoga", "Fairfield", 'Fayette', 'Franklin', 'Hamilton', 'Hancock', 'Henry', 'Huron','Medina', 'Mercer',
        'Ottawa', 'Richland', 'Sandusky', 'Shelby', 'Stark', 'Summit', 'Trumbull', 'Wayne', 'Wood', 'Wyandot']
        self.counties = counties
        self. attempt_counties = [] 
    def get_franklin(self, fpath = 'O:/Python Scripts/ev scraper/output/', fname = 'franklin.csv'):
        franklin_columns = ['SOS VOTER ID','PARTY OF BALLOT SELECTED', 'DATE REQUESTED', 'DATE MAILED', 'DATE RETURNED']
        franklin_corrected = ['SOSID','PARTYAFFIL','AVAPPDATE', 'AVSENTDATE', 'AVRECVDATE']
        df =pd.read_csv('http://boelcd.franklincountyohio.gov/assets/components/ftp.cfc?method=getOverSFTP&LocalPathName=F%3A%5C%5CBOEL%5C%5Cpublic%5C%5Cdownloads%5C%5C&RemotePathName=%2Fpublic%2Fdownloads%2F&FileName=ABSENTEE_LABELS_NEW.txt&Overwrite=true&Delete=true', delimiter = '\t')
        df = df[franklin_columns]
        df.columns = franklin_corrected
        df.to_csv('O:/Python Scripts/ev scraper/output/franklin.csv', index=False)
