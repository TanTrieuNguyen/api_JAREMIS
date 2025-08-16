from clinical_api import search_clinical_table, get_healthfinder_topics

if __name__ == "__main__":
    symptom = "fever"
    diseases = search_clinical_table(symptom)
    print(f"Các bệnh liên quan đến '{symptom}':")
    for d in diseases:
        print("-", d)
    
    print("\nDanh sách chủ đề sức khỏe từ MyHealthfinder:")
    topics = get_healthfinder_topics()
    for t in topics:
        print("-", t)
