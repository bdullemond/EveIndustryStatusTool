from tkinter import *
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
import json
from pathlib import Path

timeFormat = '%Y-%m-%d %H:%M:%S' #2014-11-13 18:24:44

class MainWindow(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, background="darkgrey")

        self.parent = parent
        self.width = 750
        self.height = 740
        self.walletTypesFileName = "walletTypes.json"
        self.itemTypesFileName = "itemTypes.json"
        self.systemNamesFileName = "systemNames.json"

        self.config = self.readDictionary("main.config")

        self.walletJournalUriTemplate = "https://api.eveonline.com/corp/WalletJournal.xml.aspx?keyID={0}&vCode={1}"
        self.industryJobsUriTemplate = "https://api.eveonline.com/corp/IndustryJobs.xml.aspx?keyID={0}&vCode={1}"
        self.marketOrdersUriTemplate = "https://api.eveonline.com/corp/MarketOrders.xml.aspx?keyID={0}&vCode={1}"
        self.typeNameUriTemplate = "https://api.eveonline.com/eve/TypeName.xml.aspx?ids={0}"
        self.mapDataUriTemplate = "https://www.fuzzwork.co.uk/api/mapdata.php?itemid={0}&format=xml"
        self.referenceTypesUri = "https://api.eveonline.com/eve/RefTypes.xml.aspx"

        self.loadCaches()
        self.itemTypeCacheDirty = False
        self.systemNameCacheDirty = False

        self.listboxHeight = 150

        self.walletListbox = Listbox(font=('courier', 8, 'normal'))
        self.industryListbox = Listbox(font=('courier', 8, 'normal'))
        self.activeMarketListbox = Listbox(font=('courier', 8, 'normal'))
        self.completeMarketListbox = Listbox(font=('courier', 8, 'normal'))

        self.initUI()
        self.parent.iconbitmap(r".\ninveah.ico")
        self.centerWindow()

    def initUI(self):
        self.parent.title("EVE Industry Status Tool")
        margin = 4

        refreshButton = Button(text="Refresh", command=self.refresh)
        refreshButton.place(x=margin, y=margin)

        walletLabel = Label(self.parent, text="Wallet Journal")
        walletLabel.place(x=margin, y=40)

        scrollbarWallet = Scrollbar()
        scrollbarWallet.place(x=self.width-20, y=60, height=self.listboxHeight)
        self.walletListbox.place(x=margin, y=60, width=self.width-24, height=self.listboxHeight)
        self.walletListbox.config(yscrollcommand=scrollbarWallet.set)
        scrollbarWallet.config(command=self.walletListbox.yview)

        industryLabel = Label(self.parent, text="Industry Jobs")
        industryLabel.place(x=margin, y=self.listboxHeight+margin+60)

        scrollbarIndustry = Scrollbar()
        scrollbarIndustry.place(x=self.width-20, y=self.listboxHeight+margin+80, height=self.listboxHeight)
        self.industryListbox.place(x=4, y=self.listboxHeight+margin+80, width=self.width-24, height=self.listboxHeight)
        self.industryListbox.config(yscrollcommand=scrollbarIndustry.set)
        scrollbarIndustry.config(command=self.industryListbox.yview)

        activeMarketLabel = Label(self.parent, text="Active Market Orders")
        activeMarketLabel.place(x=margin, y=((self.listboxHeight+margin)*2)+80)

        scrollbarActiveMarket = Scrollbar()
        scrollbarActiveMarket.place(x=self.width-20, y=((self.listboxHeight+margin)*2)+100, height=self.listboxHeight)
        self.activeMarketListbox.place(x=4, y=((self.listboxHeight+margin)*2)+100, width=self.width-24, height=self.listboxHeight)
        self.activeMarketListbox.config(yscrollcommand=scrollbarActiveMarket.set)
        scrollbarActiveMarket.config(command=self.activeMarketListbox.yview)

        completeMarketLabel = Label(self.parent, text="Complete Market Orders")
        completeMarketLabel.place(x=margin, y=((self.listboxHeight+margin)*3)+100)

        scrollbarCompleteMarket = Scrollbar()
        scrollbarCompleteMarket.place(x=self.width-20, y=((self.listboxHeight+margin)*3)+120, height=self.listboxHeight)
        self.completeMarketListbox.place(x=4, y=((self.listboxHeight+margin)*3)+120, width=self.width-24, height=self.listboxHeight)
        self.completeMarketListbox.config(yscrollcommand=scrollbarCompleteMarket.set)
        scrollbarCompleteMarket.config(command=self.completeMarketListbox.yview)

    def centerWindow(self):
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()

        x = (sw - self.width)/2
        y = (sh - self.height)/2
        self.parent.geometry('%dx%d+%d+%d' % (self.width, self.height, x, y))

    def refresh(self):
        #
        # Clear the current lists, and repopulate.
        # Re-persist the dictionary caches for system names and market item types
        #
        self.clear()
        self.setWallet()
        self.setIndustry()
        self.setMarket()
        # There may be new items looked up as part of the loading of industry and market APIs, so we need to re-persist
        # the caches
        self.saveCaches()

    def clear(self):
        #
        # Clear the current lists.
        #
        self.walletListbox.delete(0, END)
        self.industryListbox.delete(0, END)
        self.activeMarketListbox.delete(0, END)
        self.completeMarketListbox.delete(0, END)

    def saveCaches(self):
        #
        # Write out the cached dictionaries to save on load times.
        #
        if self.itemTypeCacheDirty == True:
            self.writeDictionary(self.itemTypesFileName, self.itemTypes)
        if self.systemNameCacheDirty == True:
            self.writeDictionary(self.systemNamesFileName, self.systemNames)

    def loadCaches(self):
        #
        # Write out the cached dictionaries to save on load times.
        #
        self.setWalletTypes()
        self.itemTypes = self.readDictionary('itemTypes.json')
        self.systemNames = self.readDictionary('systemNames.json')

    def setWalletTypes(self):
        #
        # Load all the wallet types from the disk.
        # If that fails, get them from the API and populate the dictionary cache
        #
        self.walletTypes = self.readDictionary(self.walletTypesFileName)
        if self.walletTypes.__len__() > 0:
            return

        # Dictionary file failed to load, get from API
        rawXml = urllib.request.urlopen(self.referenceTypesUri).read()
        eveapi = ET.fromstring(rawXml)
        rowset = eveapi[1][0]
        for aRow in rowset.findall('row'):
            self.walletTypes[aRow.get('refTypeID')] = aRow.get('refTypeName')

        self.writeDictionary(self.walletTypesFileName, self.walletTypes)

    def setWallet(self):
        #
        # Populate the wallet listbox
        #
        rawXml = urllib.request.urlopen(self.walletJournalUriTemplate.format(self.config["keyID"], self.config["vCode"])).read()
        eveapi = ET.fromstring(rawXml)
        rowset = eveapi[1][0]

        walletEntryTemplate = "{0:<20} {1:<40} {2:<18} {3:<15}"
        entry = walletEntryTemplate.format('Date', 'Type', 'Amount', 'Balance')
        self.walletListbox.insert(END, entry)
        for aRow in rowset.findall('row'):
            type = self.walletTypes[aRow.get('refTypeID')]
            entry = walletEntryTemplate.format(aRow.get('date'), type, aRow.get('amount'), aRow.get('balance'))
            self.walletListbox.insert(END, entry)

    def setIndustry(self):
        #
        # Populate the industry listbox
        #
        rawXml = urllib.request.urlopen(self.industryJobsUriTemplate.format(self.config["keyID"], self.config["vCode"])).read()
        eveapi = ET.fromstring(rawXml)
        currentTimeString = eveapi[0].text
        currentTime = datetime.strptime(currentTimeString, timeFormat)
        rowset = eveapi[1][0]

        industryEntryTemplate = "{0:<20} {1:<8} {2:<40} {3:<8} {4:<15}"
        entry = industryEntryTemplate.format('Complete Date', 'Left', 'Type', 'Runs', 'System')
        self.industryListbox.insert(END, entry)
        for aRow in rowset.findall('row'):
            rowTime = datetime.strptime(aRow.get('endDate'), timeFormat)
            days = (rowTime - currentTime).days
            if days >= 0:
                hours = round(((rowTime - currentTime).seconds) / 3600)
                timeLeft = "{0}d{1}hr".format(days,hours)
            else:
               timeLeft = "0"

            entry = industryEntryTemplate.format(aRow.get('endDate'), timeLeft, aRow.get('blueprintTypeName'), aRow.get('runs'), aRow.get('solarSystemName'))
            self.industryListbox.insert(END, entry)

    def setMarket(self):
        #
        # Populate the market listbox
        #
        rawXml = urllib.request.urlopen(self.marketOrdersUriTemplate.format(self.config["keyID"], self.config["vCode"])).read()
        eveapi = ET.fromstring(rawXml)
        rowset = eveapi[1][0]

        marketEntryTemplate = "{0:<10} {1:<40} {2:<9} {3:<15} {4:<20}"
        entry = marketEntryTemplate.format('Station', 'Type', 'Vol', "Price", "Issued" )
        self.activeMarketListbox.insert(END, entry)
        self.completeMarketListbox.insert(END, entry)

        for aRow in rowset.findall('row'):
            typeName = self.getItemType(aRow.get('typeID'))
            systemName = self.getSystemName(aRow.get('stationID'))
            state = aRow.get('orderState')
            entry = marketEntryTemplate.format(systemName, typeName, aRow.get('volRemaining'), aRow.get('price'), aRow.get('issued'))

            if state == "2": #completed
                self.completeMarketListbox.insert(END, entry)
            if state == "0": #active
                self.activeMarketListbox.insert(END, entry)

    def getItemType(self, typeID):
        #
        # Attempt to get item type from the cache, if not found, load from api
        #
        if typeID in self.itemTypes:
            return self.itemTypes[typeID]

        typeRawXml = urllib.request.urlopen(self.typeNameUriTemplate.format(typeID)).read()
        eveapi2 = ET.fromstring(typeRawXml)
        typeName = eveapi2[1][0][0].get('typeName')
        self.itemTypes[typeID] = typeName
        self.itemTypeCacheDirty = True
        return typeName

    def getSystemName(self, systemID):
        #
        # Attempt to get system name from the cache, if not found, load from api
        #
        if systemID in self.systemNames:
            return self.systemNames[systemID]

        typeRawXml = urllib.request.urlopen(self.mapDataUriTemplate.format(systemID)).read()
        eveapi2 = ET.fromstring(typeRawXml)
        systemName = eveapi2[0][4].text
        self.systemNames[systemID] = systemName
        self.systemNameCacheDirty = True
        return systemName

    def writeDictionary(self, filename, dict):
        output = json.dumps(dict)
        f = open(filename, 'w')
        f.write(output)
        f.close()

    def readDictionary(self, filename):
        p = Path(filename)
        if p.exists() == False:
            return dict()

        f = open(filename, 'r')
        input = f.read()
        if input != '':
            return json.loads(input)
        else:
            return dict()

def main():

    root = Tk()
    app = MainWindow(root)

    app.refresh()

    root.mainloop()

if __name__ == '__main__':
    main()
