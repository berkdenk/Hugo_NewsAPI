# Hugo News API Bot

This project is an automation system that fetches news from the World News API using Python, converts them into markdown files for the Hugo static site generator, and then automatically publishes this site on GitHub Pages. The project combines the power of a Python script and GitHub Actions to transform dynamic news content into a static website, adopting a completely serverless approach.

## Table of Contents

  * [About the Project](https://www.google.com/search?q=%23about-the-project)
  * [Features](https://www.google.com/search?q=%23features)
  * [Setup](https://www.google.com/search?q=%23setup)
      * [Prerequisites](https://www.google.com/search?q=%23prerequisites)
      * [Local Setup](https://www.google.com/search?q=%23local-setup)
      * [Hugo Installation](https://www.google.com/search?q=%23hugo-installation)
  * [Configuration](https://www.google.com/search?q=%23configuration)
  * [Usage](https://www.google.com/search?q=%23usage)
      * [Local Development](https://www.google.com/search?q=%23local-development)
      * [GitHub Pages Deployment](https://www.google.com/search?q=%23github-pages-deployment)
  * [Project Structure](https://www.google.com/search?q=%23project-structure)
  * [Contributing](https://www.google.com/search?q=%23contributing)
  * [License](https://www.google.com/search?q=%23license)
  * [Contact](https://www.google.com/search?q=%23contact)

## About The Project

This bot regularly fetches the latest news from the World News API. The retrieved news articles are then converted into markdown files, formatted for Hugo's post structure, and added to the static site content. Subsequently, GitHub Actions are used to automatically build this static site and publish it on GitHub Pages. This setup allows you to maintain a constantly updated news website without exposing your API key or needing a dedicated server.

## Features

  * **Automated News Fetching:** Automatically retrieves news from the World News API based on specified criteria.
  * **Hugo Integration:** Converts fetched news into Hugo-compatible markdown format.
  * **GitHub Pages Deployment:** Automatically deploys your site to GitHub Pages whenever new news is fetched or on a schedule, thanks to GitHub Actions.
  * **Serverless Approach:** Operates without the need for an external server.
  * **Secure API Key Management:** API keys are securely managed using GitHub Secrets.

## Setup

### Prerequisites

  * [Git](https://git-scm.com/)
  * [Python 3.9+](https://www.python.org/downloads/)
  * [Hugo](https://gohugo.io/getting-started/installing/) (For local development and testing)
  * [World News API Key](https://worldnewsapi.com/)

### Local Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/berkdenk/Hugo_NewsAPI.git
    cd Hugo_NewsAPI
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**

    ```bash
    pip install Flask requests apscheduler python-dotenv
    ```

    (Optional: If you have a `requirements.txt` file, use `pip install -r requirements.txt`.)

4.  **Create a `.env` file:**
    In the project root directory (`Hugo_NewsAPI`), create a file named `.env` and add your World News API key inside:

    ```
    WORLD_NEWS_API_KEY="YOUR_API_KEY"
    ```

### Hugo Installation

You need to install Hugo according to your operating system, following the [official Hugo documentation](https://gohugo.io/getting-started/installing/). Hugo will be automatically installed in the GitHub Actions environment.

## Configuration

  * **`news_bot.py`**: This file contains the news fetching logic, the conversion of news to markdown, and the Hugo content generation processes. API query parameters (country, category, etc.) and the number of news articles can be configured here.
  * **`static_site/config.toml`**: This is the Hugo configuration file.
      * `baseURL`: Should be set to match your GitHub Pages URL (e.g., `https://berkdenk.github.io/Hugo_NewsAPI/`).
      * `theme`: Specifies the name of the theme used (e.g., `"minimal"`).
      * Other Hugo settings and theme parameters are managed here.
  * **`.github/workflows/deploy.yml`**: This is the GitHub Actions workflow file.
      * Configures when the news bot will run (manual trigger, scheduled, on push).
      * Defines steps like installing necessary Python dependencies and Hugo.
      * Securely retrieves the API key from GitHub Secrets.
      * Handles GitHub Pages deployment settings.

## Usage

### Local Development

To fetch news, generate Hugo content, and preview locally:

1.  Ensure your virtual environment is activated.
2.  Run the following command in the root directory:
    ```bash
    python -c "from news_bot import run_news_processing_and_build; run_news_processing_and_build()"
    ```
    This command will fetch news and create new markdown files in the `static_site/content/posts` folder.
3.  To run the Hugo site locally, navigate to the `static_site` folder and start the Hugo server:
    ```bash
    cd static_site
    hugo server -D
    ```
    You can preview your site in your browser at `http://localhost:1313/`.

### GitHub Pages Deployment

The project is automatically deployed via GitHub Actions using the `.github/workflows/deploy.yml` file:

1.  **Add World News API Key to GitHub Secrets:**
      * In your GitHub repository, navigate to **`Settings` \> `Secrets and variables` \> `Actions`**.
      * Click on `New repository secret`.
      * Set the name to `WORLD_NEWS_API_KEY`.
      * Paste your World News API key as the value and click `Add secret`.
2.  **Verify GitHub Pages Settings:**
      * In your GitHub repository, navigate to **`Settings` \> `Pages`**.
      * Under `Build and deployment`, ensure that **`GitHub Actions`** is selected as the `Source`.
3.  **Trigger the Workflow:**
      * To manually trigger, go to the `Actions` tab, select the `Build and Deploy News Site` workflow, and click the `Run workflow` button.
      * Alternatively, it will run automatically when you push to the `main` branch or according to the scheduled (cron) setting.

After a successful deployment, your site will be published at `https://berkdenk.github.io/Hugo_NewsAPI/`.

## Project Structure

```
Hugo_NewsAPI/
├── .github/
│   └── workflows/
│       └── deploy.yml          # GitHub Actions workflow
├── news_bot.py                 # Script for fetching news and generating Hugo content
├── static_site/
│   ├── archetypes/
│   ├── content/
│   │   └── posts/              # Generated news markdown files go here
│   ├── layouts/
│   ├── static/
│   ├── themes/
│   │   └── minimal/            # Hugo minimal theme (added as Git submodule)
│   ├── config.toml             # Hugo site configuration file
│   └── hugo.toml               # Alternative to Hugo config.toml (if used)
├── .env                        # For local API key (ignored by Git)
├── .gitignore                  # Files to be ignored by Git
└── README.md                   # This file
```

## Contributing

We welcome your feedback and contributions\! Please feel free to open an "Issue" or submit a "Pull Request."

## License

This project is licensed under the [MIT License](https://www.google.com/search?q=LICENSE). (It is recommended to create a `LICENSE` file if you don't have one.)

## Contact

For any questions or feedback, feel free to reach out:

  * **GitHub:** [berkdenk](https://www.google.com/search?q=https://github.com/berkdenk)

-----
