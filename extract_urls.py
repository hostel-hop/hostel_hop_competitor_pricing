import xml.etree.ElementTree as ET
import csv
from fuzzywuzzy import fuzz

import xml.etree.ElementTree as ET
import csv
from fuzzywuzzy import fuzz

# Function to normalize the last part of the URL (replace hyphens with spaces, lowercase, etc.)
def normalize_url_part(url_part):
    return url_part.lower().replace('-', ' ')

# Function to extract URLs from XML
def extract_urls_from_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
    urls = []
    
    for url in root.findall('ns:url', namespace):
        loc = url.find('ns:loc', namespace).text
        urls.append(loc)
    
    return urls

# Function to match URLs with hostel names using fuzzy matching
def match_urls_with_hostel_names(urls, hostel_names, threshold=100):
    matched_urls = []
    matched_hostels = set()  # Set to keep track of matched hostels
    
    for url in urls:
        last_part_of_url = url.split('/')[-1]  # Extract the last part of the URL
        normalized_url_part = normalize_url_part(last_part_of_url)  # Normalize the last part of the URL
        
        for hostel_name in hostel_names:
            if hostel_name in matched_hostels:
                continue  # Skip if the hostel has already been matched
            
            if fuzz.partial_ratio(hostel_name.lower(), normalized_url_part) >= threshold:
                matched_urls.append(url)
                matched_hostels.add(hostel_name)  # Add to matched hostels
                print(f"Matched: {url} -> {hostel_name}")
                break
                
    return matched_urls

# Load hostel names from CSV
def load_hostel_names_from_csv(csv_file):
    hostel_names = []
    
    with open(csv_file, mode='r', newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            hostel_names.append(row[0])
    
    return hostel_names

# Main function
def main(xml_file, csv_file, output_file):
    urls = extract_urls_from_xml(xml_file)
    hostel_names = load_hostel_names_from_csv(csv_file)
    matched_urls = match_urls_with_hostel_names(urls, hostel_names)
    
    # Write matched URLs to output file
    with open(output_file, mode='w') as file:
        for url in matched_urls:
            file.write(f"{url}\n")
    
    print(f"Matched URLs have been saved to {output_file}")

# Example usage
if __name__ == "__main__":

    with open('hotelz_listings.xml', 'rb') as f:
        content = f.read()
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]

    with open('hotelz_listings.xml', 'wb') as f:
        f.write(content)

    xml_file = 'hotelz_listings.xml'
    csv_file = 'hostel_names.csv'
    output_file = 'matched_urls.txt'
    
    main(xml_file, csv_file, output_file)
