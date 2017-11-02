# Calendar Parser for OSM Wiki
converts Microformat calendar data on a given (wiki) page to json. Can handle easy exceptions from standard. Additionally it adds data from raw html like type of event and "big event" indication.

It provides currently: start date, end date, type of event, big event indicator, description, town, state, country 

## Contact
Send OSM message to SunCobalt

## Description
It filters so called 'h-events' and extracts  
  properties/start  
  properties/end  
  properties/name  

It then splits the comma separated properties/name into a list and assumes that  
[0] = event description  
[1] = town  
[2] = country  

If the generated list has more than 3 values it tries to read an exception format file. It is comma seperated
a,b,c,d,e,f,g

with 
```C
if (list[a] == b) and (list[c] == d) {  
    country = list[e];  
    state = list[f]; //use 99 if not available  
    town = list[g];  
}  
```
example:  
3,United Kingdom,1,Edinburgh,3,2,1
-> see error.json for info what the different fields contain

Since it is not part of the Microformat, the script also looks in the raw html data for the big event indicator (html bold formated events '<big>') and the type of the event (for example 'class="p-category" title="Mapping party")

Output example:
{"description": "Stuttgarter Stammtisch", "state": "", "end": "2017-11-02", "start": "2017-11-01", "Big": "", "country": "Germany", "town": "Stuttgart", "EventType": "Social"} 

Additonally, geolocation can be turned on. As the caching is not yet implemented, it is turned off by default


## Prerequisites
* Python3
* Geopy Geocoding lib https://github.com/geopy/geopy
* Microformat2 parser https://github.com/tommorris/mf2py
