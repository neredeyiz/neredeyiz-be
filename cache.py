from typing import Dict, Any

from constants import TODAY_PLACES, GATHERING_TIME, FINAL_PLACE, VOTES_LAST_UPDATED, VOTES


class DailyCache:
    def __init__(self):
        self._cache: Dict[str, Any] = {
            TODAY_PLACES: None,
            GATHERING_TIME: None,
            FINAL_PLACE: None,
            VOTES: {},
            VOTES_LAST_UPDATED: None
        }

    def update_places_and_time(self, today_places: str, gathering_time: str):
        self.update(TODAY_PLACES, today_places)
        self.update(GATHERING_TIME, gathering_time)

    def add_vote(self, place_name: str):
        if place_name in self.get(VOTES):
            self._cache[VOTES][place_name] += 1
        else:
            self._cache[VOTES][place_name] = 1

    def update(self, key: str, value: Any):
        self._cache[key] = value

    def get(self, key: str) -> Any:
        return self._cache.get(key)

    def reset(self):
        self._cache = {
            TODAY_PLACES: None,
            GATHERING_TIME: None,
            FINAL_PLACE: None,
            VOTES_LAST_UPDATED: None
        }


# Singleton cache instance
cache = DailyCache()