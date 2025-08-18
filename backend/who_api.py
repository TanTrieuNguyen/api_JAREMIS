import os
import requests
from typing import Any, Dict, List
from datetime import datetime
import json


class WHOAPIService:
    def __init__(self):
        self.base_url = "https://ghoapi.azureedge.net/api"
        self.cache_file = "backend/data/who_cache.json"
        self.cache_duration = 24 * 60 * 60  # 24 hours in seconds

    def _load_cache(self) -> Dict[str, Any]:
        """Load cached data"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}

    def _save_cache(self, data: Dict[str, Any]) -> None:
        """Save data to cache"""
        try:
            import os
            os.makedirs("backend/data", exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Cache save error: {e}")

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Check if cache is still valid"""
        return (datetime.now().timestamp() - timestamp) < self.cache_duration

    def get_disease_outbreaks(self) -> List[Dict[str, Any]]:
        """Lấy thông tin dịch bệnh đang bùng phát từ WHO"""
        cache = self._load_cache()
        cache_key = "disease_outbreaks"

        # Check cache first
        if (cache_key in cache and
            "timestamp" in cache[cache_key] and
            self._is_cache_valid(cache[cache_key]["timestamp"])):
            return cache[cache_key]["data"]

        try:
            # WHO Disease Outbreak News
            url = f"{self.base_url}/MALARIA_EST_DEATHS"  # Example endpoint
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()

                # Process WHO data format
                outbreaks = []
                if isinstance(data, dict) and "value" in data:
                    for item in data["value"][:20]:  # Top 20
                        if isinstance(item, dict):
                            outbreaks.append({
                                "disease": item.get("GHO", "Unknown"),
                                "region": item.get("SpatialDim", "Global"),
                                "year": item.get("TimeDim", datetime.now().year),
                                "severity": "moderate"  # Default
                            })

                # Cache result
                cache[cache_key] = {
                    "data": outbreaks,
                    "timestamp": datetime.now().timestamp()
                }
                self._save_cache(cache)
                return outbreaks

        except Exception as e:
            print(f"WHO API error: {e}")

        # Fallback: Manual curated list of common diseases
        return self._get_fallback_diseases()

    def _get_fallback_diseases(self) -> List[Dict[str, Any]]:
        """Fallback list nếu WHO API không khả dụng"""
        return [
            {"disease": "COVID-19", "severity": "high", "region": "Global"},
            {"disease": "Cúm mùa", "severity": "moderate", "region": "Global"},
            {"disease": "Cảm lạnh", "severity": "low", "region": "Global"},
            {"disease": "Viêm phổi", "severity": "moderate", "region": "Global"},
            {"disease": "Sốt xuất huyết", "severity": "high", "region": "Southeast Asia"},
            {"disease": "Tiêu chảy", "severity": "moderate", "region": "Global"},
            {"disease": "Đau đầu", "severity": "low", "region": "Global"},
            {"disease": "Tăng huyết áp", "severity": "moderate", "region": "Global"},
            {"disease": "Đái tháo đường", "severity": "moderate", "region": "Global"},
            {"disease": "Viêm dạ dày", "severity": "moderate", "region": "Global"}
        ]

    def get_popular_diseases(self, region: str = "Global") -> List[str]:
        """Lấy danh sách bệnh phổ biến theo vùng"""
        outbreaks = self.get_disease_outbreaks()

        # Filter by region và severity
        popular = []
        for outbreak in outbreaks:
            if (outbreak.get("region") == region or
                outbreak.get("region") == "Global" or
                region == "Global"):
                disease = outbreak.get("disease", "").lower()
                if disease and disease not in popular:
                    popular.append(disease)

        return popular[:15]  # Top 15


# Global instance
who_service = WHOAPIService()


# Convenience functions
def get_disease_outbreaks() -> List[Dict[str, Any]]:
    return who_service.get_disease_outbreaks()


def get_popular_diseases(region: str = "Global") -> List[str]:
    return who_service.get_popular_diseases(region)