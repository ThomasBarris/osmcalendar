# Calendar Parser for OSM Wiki
converts Microformat calendar data on a given (wiki) page to json. Can handle easy exceptions from standard 

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
if (list[a] == b) and (list[c] == d) {
	country = e;
        state = f; //use 99 if not available
	town = g;
}
example:
3,United Kingdom,1,Edinburgh,3,2,1

## Prerequisites
Ruby3
Microformat2 parser https://github.com/tommorris/mf2py
