import requests
import hashlib
import time
import random
from pydantic import BaseModel
from typing import List, Optional

PUBLIC_KEY = "1e00689c9324cb2808d5c3a4466119f2"
PRIVATE_KEY = "21e77016df37a894253303dcd4b302a1b69bad7a"

class Thumbnail(BaseModel):
    path: str
    extension:str

class ComicsInfo(BaseModel):
    available: int = 0

class MarvelCharacter(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    thumbnail: Optional[Thumbnail] = None
    comics: Optional[ComicsInfo] = None


def get_auth_params():
    ts = str(time.time())
    to_hash = ts + PRIVATE_KEY + PUBLIC_KEY
    hash_result = hashlib.md5(to_hash.encode()).hexdigest()
    return {
        "ts": ts,
        "apikey": PUBLIC_KEY,
        "hash": hash_result
    }


def fetch_characters(limit: int = 100) -> List[MarvelCharacter]:
    print("Getting the Characters...")
    url = "https://gateway.marvel.com/v1/public/characters"
    params = {"limit": limit}
    params.update(get_auth_params())

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data["data"]["results"]

        characters = [MarvelCharacter(**c) for c in results] 
        print(f"All {len(characters)} loaded successfully!\n")
        return characters 
    else:
        print("Error Fetching Marvel Characters", response.status_code)
        return []
    

def generate_description_question(characters: List[MarvelCharacter]):
    valid = [c for c in characters if c.description]
    if len (valid) < 4:
        return None
    
    correct = random.choice(valid)
    others = random.sample([c for c in valid if c.id != correct.id], 3)

    options = [correct.name] + [c.name for c in others]
    random.shuffle(options)

    return {
        "question": f"Which character matches this decsription?n\n\"{correct.description}\"",
        "options": options,
        "answer": correct.name
    }

def generate_picture_question(characters: List[MarvelCharacter]):
    valid = [
        c for c in characters 
        if c.thumbnail and " image_not_avaiable" not in c.thumbnail.path
    ]
    if len(valid) < 4:
        return None
    
    correct = random.choice(valid)
    others = random.sample([c for c in valid if c.id != correct.id], 3)

    img_url = f"{correct.thumbnail.path}/standard_xlarge.{correct.thumbnail.extension}"
    options = [correct.name] + [c.name for c in others]
    random.shuffle(options)

    return {
        "questions": f"Which Marvel character is shown in this image?\n\n{img_url}",
        "options": options,
        "answer": correct.name
    }

def generate_comic_count_question(characters: List[MarvelCharacter]):
    valid = [c for c in characters if c.comics and c.comics.available > 0]
    if len(valid) < 4:
        return None
    
    sample = random.sample(valid, 4)
    correct = max(sample, key=lambda c: c.comics.available)

    options = [c.name for c in sample]
    random.shuffle(options)

    return {
        "question": "Which of these characters has appeared in the most comics?",
        "options": options,
        "answer": correct.name
    }

def generate_trivia_question(characters: List[MarvelCharacter]):
    question_type = random.choice(["description", "picture", "comic_count"])

    if question_type =="description":
        return generate_description_question(characters)
    elif question_type == "picture":
        return generate_picture_question(characters)
    elif question_type == "comic_count":
        return generate_comic_count_question(characters)
    else:
        return None
    
#GAME LOOP
def play_game(characters: List[MarvelCharacter], num_questions: int = 5):
    print(f"Welcome to Marvel Trivia!\n")
    score = 0

    for i in range(num_questions):
        print(f"\n Question {i+1} of {num_questions}")
        question_data = None
        while question_data is None:
            question_data = generate_trivia_question(characters)

        print(question_data["question"])
        for idx, option in enumerate(question_data["options"]):
            print(f"{idx + 1}. {option}")

        try:
            choice = int(input("\nEnter you answer (1-4): "))
            if question_data ["options"][choice - 1] == question_data["answer"]:
                print("Correct!\n")
                score += 1
            else:
                print(f"Incorrect. The answer was: {question_data['answer']}\n")
        except:
            print("Invalid input, question skipped.\n")

    print(f"GAME OVER! YOU SCORED {score}/{num_questions}")
    print("Thanks for playing!")

    #RUN GAME
if __name__ == "__main__":
    characters = fetch_characters(limit=100)
    if characters:
        play_game(characters, num_questions=5)
