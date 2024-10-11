import json

def count_high_similarity_scores(file_path, threshold=60):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    count = sum(1 for item in data if item.get('similarity_score', 0) > threshold)
    
    return count

# Usage
file_path = 'hostelz_search_results.json'
high_similarity_count = count_high_similarity_scores(file_path)

print(f"Number of items with similarity score > 60: {high_similarity_count}")

