import requests
import json
import csv
from fuzzywuzzy import fuzz

def search_hostelz(hostel_info):
    name = hostel_info['name']
    query = name.replace(' ', '+')
    url = f"https://www.hostelz.com/search-autocomplete?s={query}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return find_best_suggestion(data, hostel_info)
    else:
        return None

def find_best_suggestion(data, hostel_info):
    suggestions_outer = data.get('suggestions', [])
    if len(suggestions_outer) == 0:
        return None
    suggestions = suggestions_outer[0].get('items', [])
    best_suggestion = None
    best_similarity = 0

    for suggestion in suggestions:
        suggestion_text = suggestion.get('highlighted', '')
        suggestion_text = suggestion_text.replace('<mark>', '').replace('</mark>', '')
        similarity = calculate_similarity(suggestion_text, hostel_info)
        if similarity > best_similarity:
            best_similarity = similarity
            best_suggestion = suggestion

    return (best_suggestion, best_similarity) if best_suggestion else None

def calculate_similarity(suggestion_text, hostel_info):
    match = f"{hostel_info['name']} {hostel_info['city']} {hostel_info['state']} {hostel_info['country']}".lower()
    return fuzz.partial_ratio(match, suggestion_text.lower())

def main():
    results = []
    
    with open('hostel_hop_hostel_names.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for hostel_info in reader:
            suggestion_data = search_hostelz(hostel_info)
            
            if suggestion_data:
                suggestion, similarity_score = suggestion_data
                results.append({
                    'property_hostelz_url': suggestion.get('url'),
                    'property_name': hostel_info['name'],
                    'hostel_hop_property_id': hostel_info['id'],
                    'similarity_score': similarity_score
                })
            else:
                results.append({
                    'property_name': hostel_info['name'],
                    'hostel_hop_property_id': hostel_info['id'],
                    'error_message': 'No matching suggestion found',
                    'similarity_score': 0
                })


    with open('hostelz_search_results.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    main()