import pandas as pd 
import os
import datetime

class Stitcher(object):
    def __init__(self, fpath = ''):
        '''Takes arguments: 
        
        fpath - should be a string directed to the directory where the votefind counties are 
        
        files - should be an integer enumerating the number of votefind counties were imported'''
        npath = os.getcwd()
        if fpath:
            self.fpath = fpath
        else:
            self.fpath = npath+'/output/'
        today = datetime.datetime.today()
        month = today.month
        if month < 10:
            month = '0'+str(month)
        else:
            month = str(month)
        day =today.day
        if day < 10:
            day = "0"+str(day)
        else:
            day = str(day)
        self.today = '2020'+month+day
        

    def import_vf(self, files = 40):
        '''Takes the number of votefind files to condense.'''
        df = pd.read_csv(self.fpath+'AbsenteeFile.csv', index_col='SOSID')
        needed_colums= ['PARTYAFFIL','AVAPPDATE', 'AVSENTDATE', 'AVRECVDATE','AVAPPTYPE','PHONE' ]
        df = df[needed_colums]
        dfs = []
        dfs.append(df)
        for i in range(1, files):
            try:
                df = pd.read_csv(self.fpath+'absenteefile({}).csv'.format(i+1), index_col='SOSID', low_memory = False)
                try:
                    df = df[needed_colums]
                    dfs.append(df)
                except:
                    columns_2=['PARTYAFFIL','AVAPPDATE', 'AVSENTDATE', 'AVRECVDATE','AVAPPTYPE']
                    df = df[columns_2]
                    dfs.append(df)
            except Exception as e:
                print('absenteefile({}).csv not found: {}'.format(i+1,e))

        df = pd.concat(dfs)
        df.index.names = ['sos_id']
        self.df = df
    def import_hamilton(self, fpath = 'O:/Python Scripts/ev scraper/output/'):
        files = os.listdir(self.fpath)
        fname = ''
        for i in files:
            if "AbsenteeListExport-5" in i:
                fname = i

        df_hamilton = pd.read_csv(self.fpath+fname, index_col='OVID', low_memory= False)
        hamilton_columns = ['AbsenteeParty','Request Application Date', 'Return Ballot Date','Phone']
        columns_renamed = ['PARTYAFFIL', 'AVAPPDATE', 'AVRECVDATE' ,'PHONE']
        df_hamilton = df_hamilton[hamilton_columns]
        df_hamilton.columns = columns_renamed
        df_hamilton.index.names = ['sos_id']
        dfs = []
        dfs.append(self.df)
        dfs.append(df_hamilton)
        
        print('Hamilton Appended to file.')
        df = pd.concat(dfs, sort=True)
        self.df = df
    def import_franklin(self, fpath = 'O:/Python Scripts/ev scraper/output/', fname = 'franklin.csv'):
        old_code = '''try:
            df_franklin = pd.read_csv(self.fpath+fname,  delimiter = '\t')
            franklin_columns = ['Local ID','Party', 'Date Requested','Date Mailed' , 'Date Returned']
            franklin_renamed = ['county_id','PARTYAFFIL', 'AVAPPDATE', 'AVSENTDATE', 'AVRECVDATE']
            final_columns = ['PARTYAFFIL', 'AVAPPDATE', 'AVSENTDATE', 'AVRECVDATE']
            df_franklin = df_franklin[franklin_columns]
            df_franklin.columns = franklin_renamed
            currentpath = os.getcwd()
            currentpath = currentpath + '/input/'
            fullfile = pd.read_csv(currentpath+'fullvf.csv', index_col = 'sos_id')
            fullfile = fullfile.join(df_franklin.set_index('county_id'),how = 'inner', on = 'county_id')
            df_franklin = fullfile[fullfile['county_no']==25]
            df_franklin = df_franklin[final_columns]
            df_franklin.to_csv(self.fpath+'franklin.csv')
            print("Franklin reworked.")
            dfs = []
            dfs.append(df_franklin)
            dfs.append(self.df)
            print('Franklin Appended to file.')
            df = pd.concat(dfs, sort=True)
            self.df = df'''
        try: 
            df_franklin = pd.read_csv(self.fpath+fname, delimiter = ',', index_col = 0)
            dfs = []
            dfs.append(df_franklin)
            dfs.append(self.df)
            print("Franklin appended to file")
            df = pd.concat(dfs, sort=True)
            self.df = df
        except Exception as e:
            print('Franklin Failed to import: {}'.format(e))

    def write(self, fpath = 'O:/Python Scripts/ev scraper/output/', fname ='fullfile.csv' ):
        '''Writes the collected df into a csv. Takes two arguments: 
        
        fpath - desired full file path
        
        fname - desired file name'''
        df = self.df
        df = df[df.index.get_level_values('sos_id').notna()]
        df = df[df.index.get_level_values('sos_id') != 'VN']   
        df.to_csv(self.fpath+fname)
        #df.to_csv('fullfile.zip', compression = 'zip') having trouble getting this line working. 
