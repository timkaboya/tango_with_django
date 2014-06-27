import json
import urllib, urllib2

def run_query(search_terms):
  #Specify the base
  root_url = 'https://api.datamarket.azure.com/Bing/Search/'
  source = 'Web'

  #Specify how many results we wish to be returned per page. 
  # Offset specifies where in the results list to start from. 
  # With results_per_page = 10 and offset = 11, this would start from Page 2. 
  results_per_page = 10
  offset = 0

  # Wrap quotes around our query terms as required by the Bing API. Query we will then use is stored within variable query. 
  query = "'{0}'".format(search_terms)
  query = urllib.quote(query)

  # Construct the other part of request's URL. 
  # Sets the format of the response to JSON and sets other properties.
  search_url = "{0}{1}?$format=json&$top={2}&$skip={3}&Query={4}".format(root_url, source, results_per_page, offset, query)

  #Set up auth with the Bing servers. Leave username blank and put in API Key. 
  username = ''
  bing_api_key = '4p50rcW6GE1jWE1xoViBg+eQx3VNUkxVfmCNZLRXPcA'

  #Create a 'password manager' which handles authentication for us. 
  password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
  password_mgr.add_password(None, search_url, username, bing_api_key)

  #Create our results list which we'll populate
  results = []

  try:
    # Prepare for connecting to Bing's servers
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)
    
    # Connect to the server and read the response generated
    response = urllib2.urlopen(search_url).read()

    # Convert the string response to a Python dictionary object. 
    json_response = json.loads(response)

    # Loop through each page returned, populating out results list. 
    for result in json_response['d']['results']:
      results.append({
        'title': result['Title'],
        'link': result['Url'],
        'summary': result['Description']})

    # Catch a URLError exception - something went wrong when connecting!
  except urllib2.URLError, e:
    print "Error when querying the Bing API: ", e

  #Return the list of results to the calling function. 
  return results

def main():
    search_str = []
    while True:
        search_str = raw_input("What are you looking for??")
        results = run_query(search_str)
        i = 1
        for result in results:
            print "Rank: ",i
            i = i + 1
            print "Title: ", result['title']
            print "Link: ", result['link']
            #print "Summary: ", result['summary']
if __name__ == '__main__':
    main()
