import requests

def search_clinical_table(symptom: str):
    url = "https://clinicaltables.nlm.nih.gov/api/icd10cm/v3/search"
    params = {
        "terms": symptom,
        "maxList": 10
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        print(data)  # In toàn bộ dữ liệu xem cấu trúc JSON
        return data[1] if len(data) > 1 else []
    else:
        return []

def get_healthfinder_topics():
    url = "https://health.gov/myhealthfinder/api/v3/topicsearch.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        topics = data.get("Result", {}).get("Resources", {}).get("Resource", [])
        return [t.get("Title") for t in topics]
    else:
        return []
