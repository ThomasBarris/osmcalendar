#########################################################################
# License: Public Domain                                                #
# Contact: SunCobalt@OSM                                                #
#########################################################################


import mf2py                               # Microformat2 parser https://github.com/tommorris/mf2py
import json                                # json ...as we output json files
import io                                  # and io for file handling
from geopy.geocoders import Nominatim      # geocoding lib from https://github.com/geopy/geopy
from urllib.request import urlopen         # we need to read the html file directly to recognise BIG
from time import sleep                     # Nominatim is very sensitive and we must wait between to requests
from datetime import datetime,timedelta    # for the timestamp in the output and the date adjustment
from bs4 import BeautifulSoup              # for stripping html tags from raw html for finding "big" and conference type

#########################################################################
# file and path holding the exceptions                                  #
exception_file = '/var/www/html/osmc/excp.lst'                          #
#                                                                       #
# file and path to save the json file with the results                  #
result_json = '/var/www/html/osmc/calendar.json'                        #
#                                                                       #
# file and path to store the unhandled exceptions                       #
error_json  = '/var/www/html/osmc/error.json'                           #
#                                                                       #
# where to read the html with the Microformat2 coded calendar entries   #
wiki_url = "http://wiki.openstreetmap.org/wiki/Current_events"          #
#                                                                       #
# enable geocoding (lat/lon from town/country), source Nominatim        #
geocoding = False            #True or False                             #
#                                                                       #
# file and path holding the preview html                                #
preview_file = '/var/www/html/osmc/preview.html'                        #
#                                                                       #
osmc_version = 9             #we are changing it quite often            #
#########################################################################


# functions that adjusts or converts date
# the mf2py lib returns the end date +1...for whatever reason...so function is mainly used to reduce date by -1
# fucntion held variable to allow format changes (string -> datetime object -> string
def dateMod(inputDate, modifier):
    # change the date string YYYY-mm-dd to a datetime object
    formated_date=datetime.strptime(inputDate, '%Y-%m-%d')
    #apply the modifier to the date
    modified_date = formated_date + timedelta(days=modifier)
    # convert it back to a string YYYY-mm-dd
    outputDate = modified_date.strftime('%Y-%m-%d')
    return outputDate



# reading the wiki and copy the content into a list of strings
with urlopen(wiki_url) as f:
    wiki_html_list = f.read().splitlines()

#wiki_html_list = wiki_html_list.encode('utf-8')

# reading data from the OSM Wiki site and parse it
mf_obj = mf2py.Parser(url=wiki_url,html_parser="html5lib")

# convert the data to a json string and filter events / exclude all the html stuff
## create a json string
json_obj=mf_obj.to_json(filter_by_type="h-event")

## Mit json.loads wandelt man einen String im JSON-Format, 
## hier json_obj, in Python-Elemente um die Dictionarys enthält:
formated_json = json.loads(json_obj)

# we store the combined output data here
out_array = []
out_error = []

# just a seperator for printiung
end_str = ' ** '

if (geocoding):
    try:
        # instantiate geocoder class
        geolocator = Nominatim()
    except:
        print('Geocoding not available')
        geocoding = False

# read exceptions from file
with io.open(exception_file, 'r', encoding='utf8') as excp_file:
    exception_l = excp_file.readlines()
exception_l = [x.strip('\n') for x in exception_l]

#iterate through the input json
for each in formated_json:
    # we will store the output data for a single line/event here
    out_data_line = {}
    out_error_line = {}

    # we don't now wether a date belongs to an event with errors or not, we will assign it to the appropraite dict later
    prelim_out_data = {}

    ######################reading properties START and END################################

    #not all entries have dates
    try:
        print (each['properties']['start'][0], end=end_str)
        prelim_out_data['start'] = each['properties']['start'][0]
    #if not, __-__-____
    except:
        print ('__-__-____', end=end_str)
        prelim_out_data['start'] = ''
    #same for end date
    try:
        # the mf2py lib returns the end date +1...for whatever reason...correct
        each['properties']['end'][0] = dateMod(each['properties']['end'][0],-1)


        print (each['properties']['end'][0], end=end_str)
        prelim_out_data['end'] = each['properties']['end'][0]
    except:
        print ('__-__-____', end=end_str)
        prelim_out_data['end'] = ''

    ######################reading property name###########################################

    # >>>>read property name and prepare data
    #########################################

    # under name is a string/mix of description, country, town etc, it is comma separated, split it
    string_kuddelmuddel = each['properties']['name'][0]
    kuddelmuddel_list = string_kuddelmuddel.split(",")

    # >>>> define standard (3 datafields)
    #####################################

    #usuallay we have 3 items in here, if 4 we must add an exception handling
    k_length=len(kuddelmuddel_list)

    #usually indices for....
    country = 2
    state = 99 #very uncommon, 99 for not avaivable
    town = 1
    desc = 0

    # usually the entry is not new to us, but if a new entry comes in with more or less than 3 fields, throw it for exception handling
    if (k_length == 3):
        excp = 0
    else:
        # if the are not 3 fields we handle it as error unless we set excp = 0 if we found it in the excp file
        excp = 1

    # >>>> organize data fields for exceptions i.e. 4 or more data fields in property name
    ######################################################################################

    ## if there more than 3 items in the list originating from the 'names' field, we must be careful
    if k_length >= 4:

        #iterate through the exception list loaded from the file ealier in this script and compare the current entry
        for ex_row in exception_l:
            ex_list = ex_row.split(",")
            if (k_length > int(ex_list[0]) ) and (k_length > int(ex_list[2]) ):
                if (kuddelmuddel_list[int(ex_list[0])].lstrip() == ex_list[1]) and (kuddelmuddel_list[int(ex_list[2])].lstrip() == ex_list[3]):
                    #....if found set excp to zero (valid result) and assigned the currect indices
                    excp = 0
                    country = int(ex_list[4])
                    state = int(ex_list[5])
                    town = int(ex_list[6])

    # >>>> process data for standard and defined exeptions
    ######################################################


    ## if it is a valid entry, print it and write the required values to the string
    if (excp == 0):

        # assign the dates to the dict
        out_data_line = prelim_out_data

        # >>>> write country, state, town and description

        print ('Country : ', end='')
        print (kuddelmuddel_list[country].lstrip(), end = ' / ')
        out_data_line['country'] = kuddelmuddel_list[country].lstrip()

        if state !=99:
            print ('State : ', end='')
            print (kuddelmuddel_list[state].lstrip(), end = ' / ')
            out_data_line['state'] = kuddelmuddel_list[state].lstrip()
        else:
            out_data_line['state'] = ''

        print ('Town : ', end='')
        print (kuddelmuddel_list[town].lstrip(), end = ' / ')
        out_data_line['town'] = kuddelmuddel_list[town].lstrip()

        print (kuddelmuddel_list[desc].lstrip(), end= ' ***** ')
        out_data_line['description'] = kuddelmuddel_list[desc]

        # >>>> optional geocoding

        # if geocoding was set true in settings, add lat/lon if available
        if (geocoding):
            # get location for town/country
            location = geolocator.geocode(  out_data_line['country']+out_data_line['town'])

            # wait 2 seconds to allow Nominatim to calm down
            sleep(2)

            # not every value can be translated to an address
            try:
                print((location.latitude, location.longitude), end='')
                out_data_line['latitude'] = location.latitude
                out_data_line['longitude'] = location.longitude
            except:
                out_data_line['latitude'] = ''
                out_data_line['longitude'] = ''

        # >>> processing raw html 

        # let'S check if it is a BIG event. Therefore we look for event name in raw html code and check if a <big> is in the same line
        big_code = '<big>'

        ## default is that it is not a big event
        out_data_line['Big'] = ''

        out_data_line['EventType'] = '' #nothing recognised

        ## unfortunatelly the event type is 2 lines before the event description in the html so we need to remember 2 lines history
        h_line = ''
        prev_h_line = ''
        prev_prev_h_line=''

        ## iterate through list with raw html content and remember the last 2 lines
        for html_line in wiki_html_list:
            prev_prev_h_line = prev_h_line
            prev_h_line = h_line 
            h_line = html_line.decode("utf8")

            # strip html tags from html raw line, see https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
            html_cleantext = BeautifulSoup(h_line, "html5lib").text

            ################ if event description found in raw html code lines
            # .....striped by html tags as the event description in html can be
            # "State of the Map 2018</a></b></big> (international conference)" 
            # which is not equal with Microformat description/evenmt name "State of the Map 2018 (international conference)"
            if ( html_cleantext.find(kuddelmuddel_list[desc]) >= 0 ):

                ##############.....and also the html-tag for a big event is found, set "Big":"True"
                if ( h_line.find(big_code) >= 0 ):
                    out_data_line['Big'] = 'True'
                    print ('BIG', end=' ***** ')


                ##############...find the event type in raw html, 2 lines before we found the description and set the event type
                if   ( prev_prev_h_line.find('class="p-category" title="Mapping party"') >= 0 ):
                    out_data_line['EventType'] = 'Mapping Party' #for mapping parties (with surveying) or mapathons (without)

                elif ( prev_prev_h_line.find('class="p-category" title="Social"') >= 0 ):
                    out_data_line['EventType'] = 'Social'         #for informal meetings, or just to have a beer with fellow OSM addicts.

                elif ( prev_prev_h_line.find('class="p-category" title="Meeting"') >= 0 ):
                    out_data_line['EventType'] = 'Meeting'         #for meetings at a face-to-face location or virtual

                elif ( prev_prev_h_line.find('class="p-category" title="Speaking"') >= 0 ):
                    out_data_line['EventType'] = 'Speaking'         #see below

                elif ( prev_prev_h_line.find('{{Cal|talk}}') >= 0 ): #?????????????????????????
                    out_data_line['EventType'] = 'Speaking'         #for talks/speaking events with individual or small number of talks on OSM

                elif ( prev_prev_h_line.find('class="p-category" title="Conference"') >= 0 ):
                    out_data_line['EventType'] = 'Conference'        #for conferences with several talks/panels/workshops on OSM

                elif ( prev_prev_h_line.find('class="p-category" title="Pizza') >= 0 ):
                    out_data_line['EventType'] = 'Pizza' #for hack-a-thons/mapathons involving pizza (or eating other meals, e.g. pasta-parties or brunches)

                elif ( prev_prev_h_line.find('class="p-category" title="IRC"') >= 0 ):
                    out_data_line['EventType'] = 'IRC' 	#for IRC meetings about OSM.

                elif ( prev_prev_h_line.find('class="p-category" title="TV') >= 0 ):
                    out_data_line['EventType'] = 'TV' 	#for TV/press appearances. Turn on your TV that day!

                elif ( prev_prev_h_line.find('class="p-category" title="Radio/Podcast"') >= 0 ):
                    out_data_line['EventType'] = 'Podcast' #for radio/podcast recordings

                elif ( prev_prev_h_line.find('class="p-category" title="Information') >= 0 ):
                    out_data_line['EventType'] = 'Info' #for important dates e.g OSMF election deadlines

                elif ( prev_prev_h_line.find('class="p-category" title="Miscellaneous"') >= 0 ):
                    out_data_line['EventType'] = 'Misc' #whatever


        if (out_data_line['EventType']=='' ):
            print('ERR:EventType or <span> missing', end='')
        else:
            print (out_data_line['EventType'], end='')

        # end of line/entry
        print()

        ## add the entry i.e. python dict to the list that will later be exported as json
        out_array.append(out_data_line)

    else:
        # the entries could not be read so write such entries to an error file

        # add the start date and the edn date to the error dict
        out_error_line = prelim_out_data

        # mark it with "EXC" in the console and add the data to the json with the faulty entires
        print ('EXC', end = ': ')
        print (k_length, end = ' ')
        print ('data fields', end = ' : ')
        for x in range(0,6):
            try:
                print (kuddelmuddel_list[x].lstrip(), end = '##')
                out_error_line[str(x)] = kuddelmuddel_list[x].lstrip()
            except:
                pass
        print()

        #add the error entry to the list that will be later exported as error.json or similar name as defined at the beginning
        out_error.append(out_error_line)

# create the frame around the good results with timestamp and meta data
dt = datetime.now()
timestamp = dt.strftime("%A, %d. %B %Y %I:%M%p")
print ('>>>>>>>>>>>>>>>>>>>>> report generated :', end='')
print (timestamp)
out_json = { "version": osmc_version,
             "generator": "osmcalender",
             "time": timestamp,
             "copyright": "The data is taken from http://wiki.openstreetmap.org/wiki/Template:Calendar and follows its license rules.",
             "events": out_array 
          }

# write the result to a json file at the apache root
with io.open(result_json, 'w', encoding='utf8') as json_file:
    json.dump(out_json, json_file, ensure_ascii=False, sort_keys=True)


# create the frame around the faulty results with timestamp and meta data
out_json_error = { "version": osmc_version,
                   "generator": "osmcalender",
                   "time": timestamp,
                   "copyright": "The data is taken from http://wiki.openstreetmap.org/wiki/Template:Calendar and follows its license rules.",
                   "events": out_error
                 }

# write the error list to a json file at the apache root
with io.open(error_json, 'w', encoding='utf8') as json_error:
    json.dump(out_json_error, json_error, ensure_ascii=False)

#print(*objects, sep=' ', end='\n', file=sys.stdout, flush=False)

with open(preview_file, 'w') as preview_html:
    print ('<!DOCTYPE html>'                  ,file=preview_html)
    print ('<html lang="en">'                 ,file=preview_html)
    print ('<meta charset="utf-8"/>'          ,file=preview_html)
    print ('    <body><table border="1">'     ,file=preview_html)

    print ('    <thead>'                      ,file=preview_html)
    print ('        <tr>'                     ,file=preview_html)
    print ('            <th>Start</th>'       ,file=preview_html)
    print ('            <th>End</th>'         ,file=preview_html)
    print ('            <th>Description</th>' ,file=preview_html)
    print ('            <th>City</th>'        ,file=preview_html)
    print ('            <th>Country</th>'     ,file=preview_html)
    print ('            <th>Big Event</th>'   ,file=preview_html)
    print ('            <th>Event Type</th>'  ,file=preview_html)
    print ('        </tr>'                    ,file=preview_html)
    print ('    <thead>'                      ,file=preview_html)

    print ('    <tbody>'                      ,file=preview_html)

    for result in out_json['events']:
        print ('            <tr>'                 ,file=preview_html)

        print ('                <td>',end=''      ,file=preview_html)
        print (result['start'], end=''            ,file=preview_html)
        print ('                </td>'            ,file=preview_html)

        print ('                <td>',end=''      ,file=preview_html)
        print (result['end'], end=''              ,file=preview_html)
        print ('                </td>'            ,file=preview_html)

        print ('                <td>',end=''      ,file=preview_html)
        print (result['description'], end=''      ,file=preview_html)
        print ('                </td>'            ,file=preview_html)

        print ('                <td>',end=''      ,file=preview_html)
        print (result['town'], end=''             ,file=preview_html)
        print ('                </td>'            ,file=preview_html)

        print ('                <td>',end=''      ,file=preview_html)
        print (result['country'], end=''          ,file=preview_html)
        print ('                </td>'            ,file=preview_html)

        print ('                <td>',end=''      ,file=preview_html)
        print (result['Big'], end=''              ,file=preview_html)
        print ('                </td>'            ,file=preview_html)

        print ('                <td>',end=''      ,file=preview_html)
        print (result['EventType'], end=''        ,file=preview_html)
        print ('                </td>'            ,file=preview_html)

        print ('            </tr>'                ,file=preview_html)

    print ('    </tbody>'                     ,file=preview_html)
    print ('</table>'                         ,file=preview_html)
    print ('timestamp: ',end=''               ,file=preview_html)
    print (timestamp                          ,file=preview_html)
    print ('</body></html>'                   ,file=preview_html)
