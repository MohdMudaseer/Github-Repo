from flask import Flask, render_template, request, send_file
import requests
from bs4 import BeautifulSoup
import csv
import io

app = Flask(__name__)

# Function to scrape GitHub repositories
def scrape_github_repos(topic, num_repos):
    url = f"https://github.com/topics/{topic}"
    response = requests.get(url)
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

        return render_template('index.html', repos=repos, topic=topic)

    return render_template('index.html', repos=None)

@app.route('/download_csv/<topic>/<int:num_repos>', methods=['GET'])
def download_csv(topic, num_repos):
    repos = scrape_github_repos(topic, num_repos)

    # Generate CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Repository Name', 'Repository URL', 'Stars'])
    writer.writerows(repos)

    output.seek(0)
    
    return send_file(io.BytesIO(output.getvalue().encode('utf-8')), 
                     mimetype='text/csv', 
                     as_attachment=True, 
                     attachment_filename=f"{topic}_top_{num_repos}_repos.csv")

