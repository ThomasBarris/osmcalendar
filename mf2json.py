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
from datetime import datetime              # for the timestamp in the output

#########################################################################
# file and path holding the exceptions                                  #
exception_file = 'excp.lst'                                             #
#                                                                       #
# file and path to save the json file with the results                  #
result_json = '/var/www/html/calendar.json'                             #
#                                                                       #
# file and path to store the unhandled exceptions                       #
error_json  = '/var/www/html/error.json'                                #
#                                                                       #
# where to read the html with the Microformat2 coded calendar entries   #
wiki_url = "http://wiki.openstreetmap.org/wiki/Current_events"          #
#                                                                       #
# enable geocoding (lat/lon from town/country), source Nominatim        #
geocoding = False            #True or False                             #
#                                                                       #
osmc_version = 7             #we are changing it quite often            #
#########################################################################


# reading the wiki and copy the content into a list of strings
with urlopen(wiki_url) as f:
    wiki_html_list = f.read().splitlines()

#wiki_html_list = wiki_html_list.encode('utf-8')

# reading data from the OSM Wiki site and parse it
mf_obj = mf2py.Parser(url=wiki_url)

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
    # we will store the output data for a single line here
    out_data = {}
    out_error_line = {}

    ######################reading properties START and END################################

    #not all entries have dates
    try:
        print (each['properties']['start'][0], end=end_str)
        out_data['start'] = each['properties']['start'][0]
    #if not, __-__-____
    except:
        print ('__-__-____', end=end_str)
        out_data['start'] = ''
    #same for end date
    try:
        print (each['properties']['end'][0], end=end_str)
        out_data['end'] = each['properties']['end'][0]
    except:
        print ('__-__-____', end=end_str)
        out_data['end'] = ''

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

    ## if there are 4 items in the list originating from the 'names' field, we muist be careful
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

       # >>>> write country, state, town and description

        print ('Country : ', end='')
        print (kuddelmuddel_list[country].lstrip(), end = ' / ')
        out_data['country'] = kuddelmuddel_list[country].lstrip()

        if state !=99:
            print ('State : ', end='')
            print (kuddelmuddel_list[state].lstrip(), end = ' / ')
            out_data['state'] = kuddelmuddel_list[state].lstrip()
        else:
            out_data['state'] = ''

        print ('Town : ', end='')
        print (kuddelmuddel_list[town].lstrip(), end = ' / ')
        out_data['town'] = kuddelmuddel_list[town].lstrip()

        print (kuddelmuddel_list[desc].lstrip(), end= ' ***** ')
        out_data['description'] = kuddelmuddel_list[desc]

        # >>>> optional geocoding

        # if geocoding was set true in settings, add lat/lon if available
        if (geocoding):
            # get location for town/country
            location = geolocator.geocode(  out_data['country']+out_data['town'])

            # wait 2 seconds to allow Nominatim to calm down
            sleep(2)

            # not every value can be translated to an address
            try:
                print((location.latitude, location.longitude), end='')
                out_data['latitude'] = location.latitude
                out_data['longitude'] = location.longitude
            except:
                out_data['latitude'] = ''
                out_data['longitude'] = ''

        # >>> processing raw html 

        # let'S check if it is a BIG event. Therefore we look for event name in raw html code and check if a <big> is in the same line
        big_code = '<big>'

        ## default is that it is not a big event
        out_data['Big'] = ''

        ## unfortunatelly the event type is 2 lines before the event description so we need to remember 2 lines history
        h_line = ''
        prev_h_line = ''
        prev_prev_h_line=''

        ## iterate through list with raw html content
        for html_line in wiki_html_list:
            prev_prev_h_line = prev_h_line
            prev_h_line = h_line 
            h_line = html_line.decode("utf8")

            ################ if event description found in raw html code
            if ( h_line.find(kuddelmuddel_list[desc]) >= 0 ):

                ##############.....and also the html-code for a big event is found, set "Big":"True"
                if ( h_line.find(big_code) >= 0 ):
                    out_data['Big'] = 'True'
                    print ('BIG', end='')

                ##############...find the event type in raw html, 2 lines before we found the description and set the event type
                if   ( prev_prev_h_line.find('class="p-category" title="Mapping party"') >= 0 ):
                    out_data['EventType'] = 'Mapping Party' #for mapping parties (with surveying) or mapathons (without)

                elif ( prev_prev_h_line.find('class="p-category" title="Social"') >= 0 ):
                    out_data['EventType'] = 'Social'         #for informal meetings, or just to have a beer with fellow OSM addicts.

                elif ( prev_prev_h_line.find('class="p-category" title="Meeting"') >= 0 ):
                    out_data['EventType'] = 'Meeting'         #for meetings at a face-to-face location or virtual

                elif ( prev_prev_h_line.find('class="p-category" title="Speaking"') >= 0 ):
                    out_data['EventType'] = 'Speaking'         #see below

                elif ( prev_prev_h_line.find('{{Cal|talk}}') >= 0 ): #?????????????????????????
                    out_data['EventType'] = 'Speaking'         #for talks/speaking events with individual or small number of talks on OSM

                elif ( prev_prev_h_line.find('class="p-category" title="Conference"') >= 0 ):
                    out_data['EventType'] = 'Conference'        #for conferences with several talks/panels/workshops on OSM

                elif ( prev_prev_h_line.find('class="p-category" title="Pizza') >= 0 ):
                    out_data['EventType'] = 'Pizza' #for hack-a-thons/mapathons involving pizza (or eating other meals, e.g. pasta-parties or brunches)

                elif ( prev_prev_h_line.find('class="p-category" title="IRC"') >= 0 ):
                    out_data['EventType'] = 'IRC' 	#for IRC meetings about OSM.

                elif ( prev_prev_h_line.find('class="p-category" title="TV') >= 0 ):
                    out_data['EventType'] = 'TV' 	#for TV/press appearances. Turn on your TV that day!

                elif ( prev_prev_h_line.find('class="p-category" title="Radio/Podcast"') >= 0 ):
                    out_data['EventType'] = 'Podcast' #for radio/podcast recordings

                elif ( prev_prev_h_line.find('class="p-category" title="Information') >= 0 ):
                    out_data['EventType'] = 'Info' #for important dates e.g OSMF election deadlines

                elif ( prev_prev_h_line.find('class="p-category" title="Miscellaneous"') >= 0 ):
                    out_data['EventType'] = 'Misc' #whatever

                else:
                    out_data['EventType'] = '' #nothing recognised

        # end of line/entry
        print()

        ## add the entry i.e. python dict to the list that will later be exported as json
        out_array.append(out_data)

    else:
        ## special exception for our french friends
#        try:
#            if (kuddelmuddel_list[3].lstrip() == 'France') and (kuddelmuddel_list[2].lstrip() == 'tous concernés ! Digne-les-Bains'):
#                print ('Country : ', end='')
#                print (kuddelmuddel_list[3].lstrip(), end = ' / ')
#                out_data['country'] = kuddelmuddel_list[3]
#
#                print ('Town : ', end='')
#                print ('Digne-les-Bains', end = ' / ')
#                out_data['town'] = 'Digne-les-Bains'
#
#                print (kuddelmuddel_list[0].lstrip())
#                out_data['description'] = kuddelmuddel_list[0].lstrip()
#                out_array.append(out_data)
#                excp = 0
#        except:
#            pass

        ## excp is not null and it is not the french exceptiuon....add it this as an error entry
        if excp !=0:
            print ('EXC', end = ': ')
            print (k_length, end = ' ')
            print ('data fields', end = ' : ')
            for x in range(0, 4):
                try:
                    print (kuddelmuddel_list[x].lstrip(), end = '##')
                    out_error_line[str(x)] = kuddelmuddel_list[x].lstrip()
                except:
                    pass
            print()

            #add the error entry to the list that will be later exported as error.json
            out_error.append(out_error_line)

# create the frame around the good results with timestamp and meta data
dt = datetime.now()
timestamp = dt.strftime("%A, %d. %B %Y %I:%M%p")
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


