from flask import Flask, render_template, request, send_file, flash, redirect, url_for
import requests
from bs4 import BeautifulSoup
import csv
import io
import time
import logging

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Configure logging
logging.basicConfig(level=logging.INFO)

# Function to scrape GitHub repositories
def scrape_github_repos(topic, num_repos):
    url = f"https://github.com/topics/{topic}"
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

    soup = BeautifulSoup(response.text, 'html.parser')

    repos = []
    repo_elements = soup.find_all('article', class_='border rounded color-shadow-small color-bg-subtle my-4', limit=num_repos)

    for repo in repo_elements:
        repo_name = repo.find('h3').text.strip() if repo.find('h3') else "No Name"
        repo_url = "https://github.com" + repo.find('a')['href'] if repo.find('a') else "No URL"
        
        # Handle cases where the stars element might be missing
        stars_element = repo.find('span', class_='Counter js-social-count')
        stars = stars_element.text.strip() if stars_element else "0"

        repos.append([repo_name, repo_url, stars])

    return repos

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        topic = request.form['topic']
        num_repos = int(request.form['num_repos'])
        repos = scrape_github_repos(topic, num_repos)

        if repos is None:
            flash("Failed to fetch repositories. Please try again later.", "error")
            return redirect(url_for('index'))

        return render_template('index.html', repos=repos, topic=topic)

    return render_template('index.html', repos=None)

@app.route('/download_csv/<topic>/<int:num_repos>', methods=['GET'])
def download_csv(topic, num_repos):
    repos = scrape_github_repos(topic, num_repos)

    if repos is None:
        flash("Failed to fetch repositories. Please try again later.", "error")
        return redirect(url_for('index'))

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Repository Name', 'Repository URL', 'Stars'])
    writer.writerows(repos)

    output.seek(0)
    
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), 
                     mimetype='text/csv', 
                     as_attachment=True, 
                     download_name=f"{topic}_top_{num_repos}_repos.csv")

if __name__ == '__main__':
    app.run(debug=True)
