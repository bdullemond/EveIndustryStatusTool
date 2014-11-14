from tkinter import *
import urllib
import xml.etree.ElementTree as ET
from datetime import datetime

timeFormat = '%Y-%m-%d %H:%M:%S' #2014-11-13 18:24:44

class MainWindow(Frame):

    def __init__(self, parent):
        Frame.__init__(self, parent, background="darkgrey")

        self.parent = parent
        self.width = 750
        self.height = 600

        self.walletTypes = dict()
        self.itemTypes = dict()
        self.systemNames = dict()
        self.setWalletTypes()

        self.listboxHeight = 150

        self.walletEntryTemplate = "{0:<20} {1:<40} {2:<18} {3:<15}"
        self.walletListbox = Listbox(font=('courier', 8, 'normal'))

        self.industryEntryTemplate = "{0:<20} {1:<4} {2:<40} {3:<18} {4:<15}"
        self.industryListbox = Listbox(font=('courier', 8, 'normal'))

        self.marketEntryTemplate = "{0:<10} {1:<40} {2:<7} {3:<7} {4:<15} {5:<20}"
        self.marketListbox = Listbox(font=('courier', 8, 'normal'))

        self.initUI()
        self.centerWindow()

    def initUI(self):
        self.parent.title("Ninveah Enterprises Status")
        margin = 4

        refreshButton = Button(text="Refresh", command=self.refresh)
        refreshButton.place(x=margin, y=margin)

        scrollbarWallet = Scrollbar()
        scrollbarWallet.place(x=self.width-20, y=40, height=self.listboxHeight)
        self.walletListbox.place(x=margin, y=40, width=self.width-24, height=self.listboxHeight)
        self.walletListbox.config(yscrollcommand=scrollbarWallet.set)
        scrollbarWallet.config(command=self.walletListbox.yview)

        scrollbarIndustry = Scrollbar()
        scrollbarIndustry.place(x=self.width-20, y=self.listboxHeight+margin+40, height=self.listboxHeight)
        self.industryListbox.place(x=4, y=self.listboxHeight+margin+40, width=self.width-24, height=self.listboxHeight)
        self.industryListbox.config(yscrollcommand=scrollbarIndustry.set)
        scrollbarIndustry.config(command=self.industryListbox.yview)

        scrollbarMarket = Scrollbar()
        scrollbarMarket.place(x=self.width-20, y=((self.listboxHeight+margin)*2)+40, height=self.listboxHeight)
        self.marketListbox.place(x=4, y=((self.listboxHeight+margin)*2)+40, width=self.width-24, height=self.listboxHeight)
        self.marketListbox.config(yscrollcommand=scrollbarMarket.set)
        scrollbarMarket.config(command=self.marketListbox.yview)

    def centerWindow(self):
        sw = self.parent.winfo_screenwidth()
        sh = self.parent.winfo_screenheight()

        x = (sw - self.width)/2
        y = (sh - self.height)/2
        self.parent.geometry('%dx%d+%d+%d' % (self.width, self.height, x, y))

    def refresh(self):
        #
        # Clear the current lists, and repopulate.
        #
        self.clear()
        self.setWallet()
        self.setIndustry()
        self.setMarket()

    def clear(self):
        #
        # Clear the current lists.
        #
        self.walletListbox.delete(0, END)
        self.industryListbox.delete(0, END)
        self.marketListbox.delete(0, END)

    def setWalletTypes(self):
        #
        # Load all the wallet types from the API and populate the dictionary cache
        #
        rawXml = urllib.request.urlopen("https://api.eveonline.com/eve/RefTypes.xml.aspx").read()
        eveapi = ET.fromstring(rawXml)
        rowset = eveapi[1][0]
        for aRow in rowset.findall('row'):
            self.walletTypes[aRow.get('refTypeID')] = aRow.get('refTypeName')

    def setWallet(self):
        #
        # Populate the wallet listbox
        #
        rawXml = urllib.request.urlopen("https://api.eveonline.com/corp/WalletJournal.xml.aspx?keyID=2625382&vCode=5Zy8O55ZAoVXSujd9ZD0xjYywoRFC57Cegew5uE3kOVPU8wPigpZDuKgOESFbkkL").read()
        eveapi = ET.fromstring(rawXml)
        rowset = eveapi[1][0]

        entry = self.walletEntryTemplate.format('Date', 'Type', 'Amount', 'Balance')
        self.walletListbox.insert(END, entry)
        for aRow in rowset.findall('row'):
            type = self.walletTypes[aRow.get('refTypeID')]
            entry = self.walletEntryTemplate.format(aRow.get('date'), type, aRow.get('amount'), aRow.get('balance'))
            self.walletListbox.insert(END, entry)

    def setIndustry(self):
        #
        # Populate the industry listbox
        #
        rawXml = urllib.request.urlopen("https://api.eveonline.com/corp/IndustryJobs.xml.aspx?keyID=2625382&vCode=5Zy8O55ZAoVXSujd9ZD0xjYywoRFC57Cegew5uE3kOVPU8wPigpZDuKgOESFbkkL").read()
        eveapi = ET.fromstring(rawXml)
        currentTimeString = eveapi[0].text
        currentTime = datetime.strptime(currentTimeString, timeFormat)
        self.industryListbox.insert(END, "{0} <-- Current Time".format(currentTimeString))
        rowset = eveapi[1][0]

        entry = self.industryEntryTemplate.format('Complete Date', 'Days', 'Type', 'Runs', 'System')
        self.industryListbox.insert(END, entry)
        for aRow in rowset.findall('row'):
            rowTime = datetime.strptime(aRow.get('endDate'), timeFormat)
            days = (rowTime - currentTime).days
            entry = self.industryEntryTemplate.format(aRow.get('endDate'), days, aRow.get('blueprintTypeName'), aRow.get('runs'), aRow.get('solarSystemName'))
            self.industryListbox.insert(END, entry)

    def setMarket(self):
        #
        # Populate the market listbox
        #
        rawXml = urllib.request.urlopen("https://api.eveonline.com/corp/MarketOrders.xml.aspx?keyID=2625382&vCode=5Zy8O55ZAoVXSujd9ZD0xjYywoRFC57Cegew5uE3kOVPU8wPigpZDuKgOESFbkkL").read()
        eveapi = ET.fromstring(rawXml)
        rowset = eveapi[1][0]

        entry = self.marketEntryTemplate.format('Station', 'Type', 'State', 'Vol Remaining', "Price", "Issued" )
        self.marketListbox.insert(END, entry)
        for aRow in rowset.findall('row'):
            typeName = self.getItemType(aRow.get('typeID'))
            systemName = self.getSystemName(aRow.get('stationID'))
            entry = self.marketEntryTemplate.format(systemName, typeName, aRow.get('orderState'), aRow.get('volRemaining'), aRow.get('price'), aRow.get('issued'))
            self.marketListbox.insert(END, entry)

    def getItemType(self, typeID):
        #
        # Attempt to get item type from the cache, if not found, load from api
        #
        if typeID in self.itemTypes:
            return self.itemTypes[typeID]

        typeRawXml = urllib.request.urlopen("https://api.eveonline.com/eve/TypeName.xml.aspx?ids={0}".format(typeID)).read()
        eveapi2 = ET.fromstring(typeRawXml)
        typeName = eveapi2[1][0][0].get('typeName')
        self.itemTypes[typeID] = typeName
        return typeName

    def getSystemName(self, typeID):
        #
        # Attempt to get system name from the cache, if not found, load from api
        #
        if typeID in self.systemNames:
            return self.systemNames[typeID]

        typeRawXml = urllib.request.urlopen("https://www.fuzzwork.co.uk/api/mapdata.php?itemid={0}&format=xml".format(typeID)).read()
        eveapi2 = ET.fromstring(typeRawXml)
        typeName = eveapi2[0][4].text
        self.itemTypes[typeID] = typeName
        return typeName

def main():

    root = Tk()
    app = MainWindow(root)

    app.refresh()

    root.mainloop()

if __name__ == '__main__':
    main()
