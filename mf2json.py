#########################################################################
# License: Public Domain                                                #
# Contact: SunCobalt@OSM                                                #
#########################################################################


import mf2py                      # Microformat2 parser https://github.com/tommorris/mf2py
import json                       # json ...as we output json files
import io                         # and io for file handling


#########################################################################
# file that holds the exceptions                                        #
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
#########################################################################


# reading data from the OSM Wiki site
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

# read exceptions from file
with io.open(exception_file, 'r', encoding='utf8') as excp_file:
    exception_l = excp_file.readlines()
exception_l = [x.strip('\n') for x in exception_l]

#iterate through the input json
for each in formated_json:
    # we will store the output data for a single line here
    out_data = {}
    out_error_line = {}

    #not all entries have dates
    try:
        print (each['properties']['start'][0], end=end_str)
        out_data['start'] = each['properties']['start'][0]
    #if not, __-__-____
    except:
        print ('__-__-____', end=end_str)
        out_data['start'] = '__-__-____'
    #same for end date
    try:
        print (each['properties']['end'][0], end=end_str)
        out_data['end'] = each['properties']['end'][0]
    except:
        print ('__-__-____', end=end_str)
        out_data['end'] = '__-__-____'

    # under name is a string/mix of description, country, town etc, it is comma separated, split it
    string_kuddelmuddel = each['properties']['name'][0]
    kuddelmuddel_list = string_kuddelmuddel.split(",")

    #usuallay we have 3 items in here, if 4 we must add an exception handling
    k_length=len(kuddelmuddel_list)

    #usually indices for....
    country = 2
    state = 99 #very uncommon, 99 for not avaivable
    town = 1
    desc = 0

    # usually the entry is not new to us, but if a new entry comes in with 4 fields, throw it for exception handling
    excp = 0

    ## if there are 4 items in the list originating from the 'names' field, we muist be careful
    if k_length == 4:

        ### assuming we don't know the entry. Entries with excp = 1 will be written to the error.json
        excp = 1

        #iterate through the exception list loaded from the file ealier in this script and compare the current entry
        for ex_row in exception_l:
            ex_list = ex_row.split(",")
            if (kuddelmuddel_list[int(ex_list[0])].lstrip() == ex_list[1]) and (kuddelmuddel_list[int(ex_list[2])].lstrip() == ex_list[3]):
                #....if found set excp to zero (valid result) and assigned the currect indices
                excp = 0
                country = int(ex_list[4])
                state = int(ex_list[5])
                town = int(ex_list[6])


    ## if it is a valid entry, print it and write the required values to the string
    if (excp == 0):
        print ('Country : ', end='')
        print (kuddelmuddel_list[country].lstrip(), end = ' / ')
        out_data['country'] = kuddelmuddel_list[country]

        if state !=99:
            print ('State : ', end='')
            print (kuddelmuddel_list[state].lstrip(), end = ' / ')
            out_data['state'] = kuddelmuddel_list[state]
        else:
            out_data['state'] = ''

        print ('Town : ', end='')
        print (kuddelmuddel_list[town].lstrip(), end = ' / ')
        out_data['town'] = kuddelmuddel_list[town]

        print (kuddelmuddel_list[desc].lstrip())
        out_data['description'] = kuddelmuddel_list[desc]


        ## add the entry to the list that will later be exported as json
        out_array.append(out_data)

    else:
        ## special exception for our french friends
        if (kuddelmuddel_list[3].lstrip() == 'France') and (kuddelmuddel_list[2].lstrip() == 'tous concernés ! Digne-les-Bains'):
            print ('Country : ', end='')
            print (kuddelmuddel_list[3].lstrip(), end = ' / ')
            out_data['country'] = kuddelmuddel_list[3]

            print ('Town : ', end='')
            print ('Digne-les-Bains', end = ' / ')
            out_data['town'] = 'Digne-les-Bains'

            print (kuddelmuddel_list[0].lstrip())
            out_data['description'] = kuddelmuddel_list[0].lstrip()
            out_array.append(out_data)

        ## excp is not null and it is not the french exceptiuon....add it this as an error entry
        else:
            print ('EXC ', end = ":")
            for x in range(0, 4):
                print (kuddelmuddel_list[x].lstrip(), end = '##')
                out_error_line[str(x+1)] = kuddelmuddel_list[x].lstrip()
            print()

            #add the error entry to the list that will be later exported as error.json
            out_error.append(out_error_line)


# write the result to a json file at the apache root
with io.open(result_json, 'w', encoding='utf8') as json_file:
    json.dump(out_array, json_file, ensure_ascii=False)

# write the error list to a json file at the apache root
with io.open(error_json, 'w', encoding='utf8') as json_error:
    json.dump(out_error, json_error, ensure_ascii=False)


