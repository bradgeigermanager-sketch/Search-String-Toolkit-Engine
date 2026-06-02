from collections import defaultdict
import re
import math
import time
from typing import List, Dict, Any, Optional

class SearchStringConstructor:
    """Handles parsing, tokenization, and syntactic normalization of strings."""
    def __init__(self, stop_words: Optional[set] = None):
        self.stop_words = stop_words or {'the', 'a', 'an', 'and', 'or', 'in', 'of', 'for', 'to', 'is', 'on'}
        
    def normalize(self, raw_string: str) -> str:
        """Cleans syntax, strips punctuation, and normalizes casing."""
        string_clean = raw_string.lower().strip()
        string_clean = re.sub(r'[^\w\s\-\"\:]', '', string_clean)  # Keep quotes, hyphens, colons
        tokens = string_clean.split()
        # Preserve multi-word expressions but clean generic noise tokens
        filtered_tokens = [t for t in tokens if t not in self.stop_words]
        return " ".join(filtered_tokens)

    def extract_metadata(self, clean_string: str) -> Dict[str, Any]:
        """Calculates specific lexical attributes of the search string."""
        tokens = clean_string.split()
        return {
            "token_count": len(tokens),
            "has_operators": any(op in clean_string for op in ['AND', 'OR', 'NOT', ':', '"']),
            "char_length": len(clean_string)
        }


class SearchMetricsTracker:
    """Maintains transactional usage metrics for specific search strings."""
    def __init__(self):
        self.frequency = 0
        self.success_clicks = 0
        self.zero_result_events = 0
        self.execution_times: List[float] = []
        self.last_used = 0.0

    def record_execution(self, clicked: bool, zero_results: bool, duration: float):
        """Updates internal metric records per invocation."""
        self.frequency += 1
        self.last_used = time.time()
        self.execution_times.append(duration)
        if clicked:
            self.success_clicks += 1
        if zero_results:
            self.zero_result_events += 1

    @property
    def avg_execution_time(self) -> float:
        return sum(self.execution_times) / len(self.execution_times) if self.execution_times else 0.0


class HighValueSearchEngine:
    """The central construction engine to locate and store reusable searches."""
    def __init__(self, high_value_threshold: float = 15.0):
        self.constructor = SearchStringConstructor()
        self.registry: Dict[str, SearchMetricsTracker] = defaultdict(SearchMetricsTracker)
        self.metadata_store: Dict[str, Dict[str, Any]] = {}
        self.threshold = high_value_threshold

    def process_search(self, raw_string: str, clicked: bool = False, zero_results: bool = False, duration: float = 0.01):
        """Ingests a transactional search string, evaluates it, and registers it."""
        clean_string = self.constructor.normalize(raw_string)
        if not clean_string:
            return
        
        # Track historical execution metrics
        self.registry[clean_string].record_execution(clicked, zero_results, duration)
        
        # Store metadata if new
        if clean_string not in self.metadata_store:
            self.metadata_store[clean_string] = self.constructor.extract_metadata(clean_string)

    def calculate_value_score(self, clean_string: str) -> float:
        """
        Engine heuristic scoring algorithm. Calculates reusable value using:
        - Frequency (Volume of intent)
        - Engagement (Click-through rates)
        - Complexity (Long-tail vs short generic searches)
        - Penalty for zero-result failures
        """
        metrics = self.registry[clean_string]
        meta = self.metadata_store[clean_string]
        
        if metrics.frequency == 0:
            return 0.0
            
        ctr = metrics.success_clicks / metrics.frequency
        fail_rate = metrics.zero_result_events / metrics.frequency
        
        # Heuristic scoring components
        frequency_score = math.log1p(metrics.frequency) * 3.0
        ctr_bonus = ctr * 10.0
        complexity_bonus = 2.0 if meta["has_operators"] or meta["token_count"] >= 3 else 0.5
        penalty = fail_rate * 12.0
        
        total_score = frequency_score + ctr_bonus + complexity_bonus - penalty
        return round(max(0.0, total_score), 2)

    def get_high_value_library(self) -> List[Dict[str, Any]]:
        """Filters, aggregates, and ranks high-value reusable templates."""
        library = []
        for clean_string in self.registry.keys():
            score = self.calculate_value_score(clean_string)
            if score >= self.threshold:
                library.append({
                    "search_string": clean_string,
                    "value_score": score,
                    "metrics": {
                        "invocations": self.registry[clean_string].frequency,
                        "success_rate": f"{ (self.registry[clean_string].success_clicks / self.registry[clean_string].frequency) * 100:.1f}%"
                    },
                    "structural_data": self.metadata_store[clean_string]
                })
        return sorted(library, key=lambda x: x["value_score"], reverse=True)


# =====================================================================
# Engine Validation & Execution Pipeline
# =====================================================================
if __name__ == "__main__":
    engine = HighValueSearchEngine(high_value_threshold=10.0)

    # Simulated runtime log entries
    searches = [
        # A high-complexity query that consistently works and converts
        ("site:linkedin.com/in AND \"python developer\" AND \"san francisco\"", True, False, 0.05),
        ("site:linkedin.com/in AND \"python developer\" AND \"san francisco\"", True, False, 0.04),
        ("site:linkedin.com/in AND \"python developer\" AND \"san francisco\"", True, False, 0.06),
        
        # A repetitive generic lookup (high frequency, lower contextual value)
        ("python tutorial", True, False, 0.01),
        ("python tutorial", False, False, 0.01),
        ("python tutorial", True, False, 0.01),
        
        # A broken search string producing zero results (penalized out of library)
        ("python developer code hackathon error 4040404", False, True, 0.02),
        ("python developer code hackathon error 4040404", False, True, 0.02),
    ]

    for raw, clicked, zero_res, runtime in searches * 3: # Multiply array to simulate volume
        engine.process_search(raw, clicked=clicked, zero_results=zero_res, duration=runtime)

    # Extract constructed tool library
    high_value_library = engine.get_high_value_library()
    
    print(f"--- CONSTRUCTED HIGH-VALUE TOOLKIT ({len(high_value_library)} Strings Identified) ---")
    for item in high_value_library:
        print(f"\nString: [{item['search_string']}]")
        print(f" -> Value Score: {item['value_score']}")
        print(f" -> Invocations: {item['metrics']['invocations']} | Conversion Rate: {item['metrics']['success_rate']}")
