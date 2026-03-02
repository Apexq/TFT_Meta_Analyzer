import logging
import os
import random
import time
from collections import deque

import requests

from analyze import analyze_matches
from generate_readme import generate_readme

TR1_BASE = "https://tr1.api.riotgames.com"
EUROPE_BASE = "https://europe.api.riotgames.com"


class RiotClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"X-Riot-Token": api_key})
        self.req_last_second = deque()
        self.req_last_two_min = deque()

    def _throttle(self):
        now = time.monotonic()
        while self.req_last_second and now - self.req_last_second[0] >= 1:
            self.req_last_second.popleft()
        while self.req_last_two_min and now - self.req_last_two_min[0] >= 120:
            self.req_last_two_min.popleft()

        sleep_for = 0
        if len(self.req_last_second) >= 20:
            sleep_for = max(sleep_for, 1 - (now - self.req_last_second[0]))
        if len(self.req_last_two_min) >= 100:
            sleep_for = max(sleep_for, 120 - (now - self.req_last_two_min[0]))
        if sleep_for > 0:
            time.sleep(sleep_for)

    def get(self, url, params=None):
        backoff = 1
        for _ in range(5):
            self._throttle()
            response = self.session.get(url, params=params, timeout=20)
            now = time.monotonic()
            self.req_last_second.append(now)
            self.req_last_two_min.append(now)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait_time = int(retry_after) if retry_after and retry_after.isdigit() else backoff
                logging.warning("Rate limited. Sleeping %s seconds.", wait_time)
                time.sleep(wait_time)
                backoff = min(backoff * 2, 30)
                continue
            response.raise_for_status()
            return response.json()
        raise RuntimeError(f"Failed after retries: {url}")


def fetch_master_plus_entries(client):
    endpoints = [
        "/tft/league/v1/challenger",
        "/tft/league/v1/grandmaster",
        "/tft/league/v1/master",
    ]
    all_entries = []
    for endpoint in endpoints:
        payload = client.get(f"{TR1_BASE}{endpoint}")
        all_entries.extend(payload.get("entries", []))
    return all_entries


def pick_players(entries, count=10):
    if len(entries) <= count:
        return entries
    return random.sample(entries, count)


def fetch_player_results(client, player_entry):
    summoner_id = player_entry["summonerId"]
    summoner = client.get(f"{TR1_BASE}/tft/summoner/v1/summoners/{summoner_id}")
    puuid = summoner["puuid"]
    match_ids = client.get(
        f"{EUROPE_BASE}/tft/match/v1/matches/by-puuid/{puuid}/ids",
        params={"start": 0, "count": 20},
    )

    results = []
    for match_id in match_ids:
        match = client.get(f"{EUROPE_BASE}/tft/match/v1/matches/{match_id}")
        participants = match.get("info", {}).get("participants", [])
        participant = next((p for p in participants if p.get("puuid") == puuid), None)
        if participant:
            results.append({"participant": participant, "match_info": match.get("info", {})})
    return results


def run():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        raise EnvironmentError("RIOT_API_KEY is not set.")

    client = RiotClient(api_key)
    entries = fetch_master_plus_entries(client)
    if not entries:
        raise RuntimeError("No Master+ players were returned from Riot API.")

    selected_players = pick_players(entries, count=10)
    logging.info("Selected %s players for analysis.", len(selected_players))

    all_results = []
    for index, player in enumerate(selected_players, start=1):
        logging.info("Fetching player %s/%s", index, len(selected_players))
        all_results.extend(fetch_player_results(client, player))

    report = analyze_matches(all_results)
    generate_readme(report, output_path="README.md")
    logging.info("README.md updated successfully.")


if __name__ == "__main__":
    run()
