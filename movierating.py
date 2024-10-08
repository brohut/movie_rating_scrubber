import requests
from bs4 import BeautifulSoup
from imdb import IMDb
import pandas as pd
import json
#import openai  # I don't want to pay for this :(
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import google.generativeai as genai
import os

#generate your own api key here: https://ai.google.dev/gemini-api/docs/quickstart?lang=python
genai.configure(api_key=os.environ["API_KEY"])

def get_imdb_score(movie_title):
    ia = IMDb()
    movies = ia.search_movie(movie_title)
    
    if movies:
        movie = movies[0]  # Get the first search result
        ia.update(movie)    # Fetch additional information
        return movie.get('rating')
    return None

def get_rotten_tomatoes_score_bs(movie_title, movie_year):
    # Create a formatted movie title for the URL
    formatted_title = movie_title.replace(" ", "_").lower()
    #url = f"https://www.rottentomatoes.com/m/{formatted_title}"
    url = google_search('Rotten Tomatoes '+ movie_title + ' ' + str(movie_year))

    response = requests.get(url)
    
    if response.status_code == 200:
        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find the score element; this may vary with Rotten Tomatoes' site structure
            item=soup.select_one('script[data-json="reviewsData"]').text
            json_object = json.loads(item)
            critic_data = json_object['criticsScore']
            critic_score = critic_data['score']
            audience_data = json_object['audienceScore']
            audience_score = audience_data['score']
            if critic_score and audience_score:
                return [critic_score, audience_score]
            elif not critic_score and audience_score:
                return [None, audience_score]
            elif critic_score and not audience_score:
                return [critic_score, None]
            else:
                return [None, None]
        except:
            return [None, None]
    
    return [None, None]


def parse_first_column(excel_file_path, sheet_name=0):
    """
    Parses the first column of an Excel sheet into a list.
    
    :param excel_file_path: Path to the Excel file.
    :param sheet_name: The name or index of the sheet to read (default is the first sheet).
    :return: List of values from the first column.
    """
    # Read the Excel file
    df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
    
    # Extract the first column and convert it to a list
    first_column_list = df.iloc[:, 0].tolist()
    
    return first_column_list

def google_search(query):
    # Format the search query
    query = '+'.join(query.split())
    url = f'https://www.google.com/search?q={query}'
    
    # Set a user-agent to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    # Send the request to Google
    response = requests.get(url, headers=headers)
    
    # Parse the response
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find the first search result's link
    first_result = soup.find('h3')
    if first_result:
        # Navigate to the link of the first result
        link = first_result.find_parent('a')['href']
        return link
    else:
        return None


# Trying to use chatgpt for free, but this is crashing
# def query_chatgpt(prompt):
#     # Set up the Selenium WebDriver (make sure to specify the correct path to your driver)
#     PATH_TO_CHROMEDRIVER = '/usr/bin/chromedriver' # sudo apt-get install chromium-chromedriver

#     driver = webdriver.Chrome() #executable_path=PATH_TO_CHROMEDRIVER)  # Update this path

#     try:
#         # Navigate to the ChatGPT login page
#         driver.get('https://chat.openai.com')

#         # Wait for the page to load
#         time.sleep(5)  # Adjust the sleep time as needed

#         # Find the input field for the chat
#         input_field = driver.find_element(By.CSS_SELECTOR, 'textarea')  # Update this if the selector changes

#         # Type the prompt into the input field
#         input_field.send_keys(prompt)

#         # Submit the prompt
#         input_field.send_keys('\n')  # Press Enter

#         # Wait for the response to load
#         time.sleep(5)  # Adjust the sleep time as needed

#         # Find the response
#         response_elements = driver.find_elements(By.CSS_SELECTOR, '.message')  # Update this if the selector changes
#         response = response_elements[-1].text  # Get the latest response

#         return response

#     finally:
#         driver.quit()  # Close the browser

def main():
    # Read the Excel file
    df = pd.read_excel("Movie_List.xlsx", sheet_name=0)
    model = genai.GenerativeModel("gemini-1.5-flash")
    # Extract the first column and convert it to a list
    movie_titles = df.iloc[:, 0].tolist()
    movie_years = df.iloc[:, 1].tolist()
    f = open("results.txt", "a")
    for movie_title, movie_year in zip(movie_titles, movie_years):
        imdb_score = get_imdb_score(movie_title)
        rotten_score, popcorn_score = get_rotten_tomatoes_score_bs(movie_title, movie_year)
        try: 
            response = model.generate_content("Write me a 1 sentence summary for the " + str(movie_year) + " movie titled " + movie_title)
            summary = response.text
        except:
            summary = "No summary available.\n"
        print(f"Movie: {movie_title}  IMDb Score: {imdb_score}  Rotten Tomatoes Score: {rotten_score}  Rotten Popcorn Score: {popcorn_score}  Summary: {summary}")
        f.write(f"{imdb_score} : {rotten_score} : {popcorn_score} : {summary}")
        time.sleep(5) #sleep 5 seconds to stay in free tier of google ai 
    f.close()

if __name__ == "__main__":
    main()


