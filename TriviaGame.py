import requests
import hashlib # MD5 hash for API
import time # for the timestamps
import random # for random questions and multple choice
from pydantic import BaseModel
from typing import List, Optional
# both keys
PUBLIC_KEY = "1e00689c9324cb2808d5c3a4466119f2"
PRIVATE_KEY = "21e77016df37a894253303dcd4b302a1b69bad7a"
# for the image
class Thumbnail(BaseModel):
    path: str
    extension:str

class ComicsInfo(BaseModel):
    available: int = 0 # number of comics character has appeared in 
# character attributes
class MarvelCharacter(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    thumbnail: Optional[Thumbnail] = None
    comics: Optional[ComicsInfo] = None


def get_auth_params():
    ts = str(time.time()) # timestamp for each request
    to_hash = ts + PRIVATE_KEY + PUBLIC_KEY # both keys concatenated
    hash_result = hashlib.md5(to_hash.encode()).hexdigest() # MD5 hash
    # return parameters
    return {
        "ts": ts,
        "apikey": PUBLIC_KEY,
        "hash": hash_result
    }

# getting 100 marvel characters for the game
def fetch_characters(limit: int = 100) -> List[MarvelCharacter]:
    print("Getting the Characters...")
    url = "https://gateway.marvel.com/v1/public/characters"
    params = {"limit": limit}
    params.update(get_auth_params())
    # send http request to API endpoint
    response = requests.get(url, params=params)
    # gives us readable json if it is successful
    if response.status_code == 200:
        data = response.json()
        results = data["data"]["results"]

        characters = [MarvelCharacter(**c) for c in results] 
        print(f"All {len(characters)} loaded successfully!\n")
        return characters 
    else:
        # error indicating getting the characters failed
        print("Error Fetching Marvel Characters", response.status_code)
        return []
    
# description question
def generate_description_question(characters: List[MarvelCharacter]):
    # character must have a description
    valid = [c for c in characters if c.description]
    # ensure we have 4 characters
    if len (valid) < 4:
        return None
    # pick the correct answer
    correct = random.choice(valid)
    # select 3 other characters to be the incorrect answers
    others = random.sample([c for c in valid if c.id != correct.id], 3)
    # combine correct and incorrect options
    options = [correct.name] + [c.name for c in others]
    random.shuffle(options)
    # final question strcuture
    return {
        "question": f"Which character matches this decsription?n\n\"{correct.description}\"",
        "options": options,
        "answer": correct.name
    }
# picture question
def generate_picture_question(characters: List[MarvelCharacter]):
    # only characters with an image
    valid = [
        c for c in characters 
        if c.thumbnail and " image_not_avaiable" not in c.thumbnail.path
    ]
    if len(valid) < 4:
        return None
    # choose one character for the correct answer
    correct = random.choice(valid)
    others = random.sample([c for c in valid if c.id != correct.id], 3)
    # construct image based on thumbnail strcture
    img_url = f"{correct.thumbnail.path}/standard_xlarge.{correct.thumbnail.extension}"
    options = [correct.name] + [c.name for c in others]
    random.shuffle(options)

    return {
        "question": f"Which Marvel character is shown in this image?\n\n{img_url}",
        "options": options,
        "answer": correct.name
    }
# comic count question
def generate_comic_count_question(characters: List[MarvelCharacter]):
    # only characters with comic book appearences
    valid = [c for c in characters if c.comics and c.comics.available > 0]
    if len(valid) < 4:
        return None
    # rnadomly select 4 characters
    sample = random.sample(valid, 4)
    # determine which has the most comic appearences
    correct = max(sample, key=lambda c: c.comics.available)
    # generate multiple choice options
    options = [c.name for c in sample]
    random.shuffle(options)

    return {
        "question": "Which of these characters has appeared in the most comics?",
        "options": options,
        "answer": correct.name
    }
# generate trivia question
def generate_trivia_question(characters: List[MarvelCharacter]):
    question_type = random.choice(["description", "picture", "comic_count"])
    # if statement choosing which type of question
    if question_type =="description":
        return generate_description_question(characters)
    elif question_type == "picture":
        return generate_picture_question(characters)
    elif question_type == "comic_count":
        return generate_comic_count_question(characters)
    else:
        return None
    
# game loop
def play_game(characters: List[MarvelCharacter], num_questions: int = 5):
    print(f"Welcome to Marvel Trivia!\n")
    # initialize the players score
    score = 0

    for i in range(num_questions):
        print(f"\n Question {i+1} of {num_questions}")
        # generate a trivia question
        question_data = None
        while question_data is None:
            question_data = generate_trivia_question(characters)
        # display question text
        print(question_data["question"])
        # print multiple choice options
        for idx, option in enumerate(question_data["options"]):
            print(f"{idx + 1}. {option}")
        # get and validate player input
        try:
            choice = int(input("\nEnter you answer (1-4): "))
            # make sure the users input is within the valid range
            if question_data ["options"][choice - 1] == question_data["answer"]:
                print("Correct!\n")
                score += 1
            else:
                print(f"Incorrect. The answer was: {question_data['answer']}\n")
        except:
            # skip non integer inputs
            print("Invalid input, question skipped.\n")
    # summary of the users final score
    print(f"GAME OVER! YOU SCORED {score}/{num_questions}")
    print("Thanks for playing!")

    # run the game
if __name__ == "__main__":
    # fetch up to 100 characters
    characters = fetch_characters(limit=100)
    if characters:
        play_game(characters, num_questions=5)