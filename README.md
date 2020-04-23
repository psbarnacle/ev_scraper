votefind_2020p v2.0

Collects early vote files for 2020 elections. 

Install dependencies on windows using windows-install.bat
Linux-installer will only place geckodriver into the path. pandas, selenium, and bs4 are all required, and can be installed using 
pip --install bs4
pip --install selenium
pip --install pandas


The javascript filenames of the various votefind counties can be programmed under self.election_name 
list in the __init__(self) function in the Browser class.

Scraper runs with either command line on scraper.py or through the run_scraper batch file. 

geckodriver application, ohiodistricts, and stitcher are all required. 

/input/ folder contains county lists for determining which counties to search for. It also contains the default firefox profile documents:
handlers.json
prefs.js 

Downloaded files will default to the /output/+month+day+hour+minute/ folder. 