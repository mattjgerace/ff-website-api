import os
import json

def write_sample_json(data):
    current_dir = os.path.dirname(__file__)

    # Path to sample.json in the same directory
    file_path = os.path.join(current_dir, "sample.json")

    # Write JSON with indentation for readability
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4)

    return file_path

data = {}
for i in range(1, 13):
    for j in range(0, 10):
        data[f"{i}0{j}"] = {
        "active": True,
        "age": 1,
        "birth_city": None,
        "birth_country": None,
        "birth_date": "01/01/1000",
        "birth_state": None,
        "college": "Test",
        "depth_chart_order": 1,
        "depth_chart_position": "QB",
        "espn_id": int(f"{i}0{j}"),
        "fantasy_data_id": int(f"{i}0{j}"),
        "fantasy_positions": [
            "QB"
        ],
        "first_name": "Test",
        "gsis_id": " 00-0035525",
        "hashtag": "#test-NFL-SEA-0",
        "height": "1",
        "high_school": "Test",
        "injury_body_part": None,
        "injury_notes": None,
        "injury_start_date": None,
        "injury_status": "NA",
        "last_name": "Test",
        "metadata": None,
        "news_updated": 1,
        "number": 1,
        "pandascore_id": None,
        "_id": int(f"{i}0{j}"),
        "player_id": int(f"{i}0{j}"),
        "position": "QB",
        "practice_description": None,
        "practice_participation": "NA",
        "rotowire_id": 1,
        "rotoworld_id": 1,
        "search_first_name": "Test",
        "search_full_name": "TestTest",
        "search_last_name": "Test",
        "search_rank": 9999999,
        "sport": "NFL",
        "sportradar_id": "test",
        "stats_id": None,
        "status": "ACTIVE",
        "swish_id": int(f"{i}0{j}"),
        "team": "SEA",
        "weight": "1",
        "yahoo_id": int(f"{i}0{j}"),
        "years_exp": 1
        }
    data[str(662+i)] = {
        "active": True,
        "age": 1,
        "birth_city": None,
        "birth_country": None,
        "birth_date": "01/01/1000",
        "birth_state": None,
        "college": "Test",
        "depth_chart_order": 1,
        "depth_chart_position": "QB",
        "espn_id": str(662+i),
        "fantasy_data_id": str(662+i),
        "fantasy_positions": [
            "QB"
        ],
        "first_name": "Test",
        "gsis_id": " 00-0035525",
        "hashtag": "#test-NFL-SEA-0",
        "height": "1",
        "high_school": "Test",
        "injury_body_part": None,
        "injury_notes": None,
        "injury_start_date": None,
        "injury_status": "NA",
        "last_name": "Test",
        "metadata": None,
        "news_updated": 1,
        "number": 1,
        "pandascore_id": None,
        "player_id": str(662+i),
        "position": "QB",
        "practice_description": None,
        "practice_participation": "NA",
        "rotowire_id": 1,
        "rotoworld_id": 1,
        "search_first_name": "Test",
        "search_full_name": "TestTest",
        "search_last_name": "Test",
        "search_rank": 9999999,
        "sport": "NFL",
        "sportradar_id": "test",
        "stats_id": None,
        "status": "ACTIVE",
        "swish_id": str(662+i),
        "team": "SEA",
        "weight": "1",
        "yahoo_id": str(662+i),
        "years_exp": 1,
        "_id": int(f"{i}0{j}")
    }
    write_sample_json(data)