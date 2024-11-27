#!/usr/bin/env python

# Example usage:
# ./search-rfc.py mirror/in-notes/ oauth

import os
import sys
import json

# Takes a path to a directory containing RFC json files.
# Returns two dictionaries
# 1 index, a map of keywords to RFC numbers
# 2 titles, a map of RFC numbers to RFC titles
def index_rfcs(path):
    index = {}
    titles = {}
    
    for filename in os.listdir(path):
        if not filename.endswith(".json"):
            continue
            
        with open(os.path.join(path, filename)) as file:
            data = json.load(file)
        
        titles[data["doc_id"]] = data["title"]
        keywords = data["keywords"] + [data["title"], data["abstract"]]
        number = data["doc_id"]
        
        for keyword in keywords:
            if keyword not in index:
                index[keyword] = []
                
            index[keyword].append(number)
            
    return index, titles


def search_rfcs(query, index):
    results = []
    for keyword in index:
        if not keyword:
            continue
        if query.lower() in keyword.lower():
            results.extend(index[keyword])
            
    return list(set(results)) # Remove duplicates


if __name__ == "__main__":
    path = sys.argv[1]  # Path to the directory containing RFC JSON files
    query = sys.argv[2] # Search term provided by user
    
    rfc_index, rfc_titles = index_rfcs(path)
    results = search_rfcs(query, rfc_index)
    results.sort()
    for result in results:
        print("{}: {}".format(result, rfc_titles[result]))
