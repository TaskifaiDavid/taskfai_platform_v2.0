A few things to consider. 


#Aromateque - 
uses same document, they just add to existing document each month.So there need to be a built in check
what months have been reported. reports in EURO. have defined how many qt they have sold per store. Needs store/online analysis

#BOXNOX
Reports monthly
uses POS as their store/online identifier
reports in EUR
uses same document, they just add to existing document each month.So there need to be a built in check

#Creme de la creme
Reports monthly
uses "e-shop" for online and store names on the other.
reports in euro
uses EAN, needs to be converted to functional name in supabase

#Galilu
Reports monthly
uses sheet: split by store to defined quantity sold per store
dont use EAN/functional name - needs to be converted / matched in database to find ean/funcitonal name
needs to fetch price from database

#Liberty
The biggest so far most important
uses their own product number/ name
defines between Flagship = physical store and online = online
Uses sales inc VAT
Uses GBP
() = returns
using two rows per product, with same amount, make sure not to extract both per product

#Selfridges
reports weekly
have 4 physical stores and 1 online
reports one column sales and one quantity
uses same document, just fills out sales that week.

#Skins NL
Uses sales per store/online in the sheet: SalesPerLocation
reports in EURO
Reports internally to South Africa, they will stop doing this after september 2025
also repots sales per sku but on that sheet, its not defined how many qt.
uses EAN code in sales per sku
defines month in sheet: info

#Skins SA
South africa
uses same document
reports in RAND (ZAR) currency
reports what month and year
 reports both netsales and exvatnetsales
 Stockcode=EAN
 Defines store/online - ON = Online - rest is stores (column A)
  
