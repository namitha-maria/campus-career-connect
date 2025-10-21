Campus Career Connect

A comprehensive platform connecting students with alumni for career guidance.

🚀 Table of Contents

About

Features

Tech Stack

Getting Started

Prerequisites

Installation

Configuration

Running the App

Usage

Project Structure

Contributing

License

Contact

About

Campus Career Connect is designed to bridge the gap between students and alumni by providing a structured way for alumni to share insights, and students to develop skills through tests, challenges and interaction. The goal is to create a unified dashboard where students can:

take aptitude & coding tests

attend mock interviews

ask questions to alumni

track their progress over time

It’s perfect for educational institutions, career cells and student communities wanting to give structured career‑support.

Features

📝 Aptitude Tests – battery of multiple‑choice questions covering quantitative, logical, verbal reasoning.

💻 Coding Challenges – tasks for students to solve, evaluate themselves or receive alumni feedback.

🎤 Mock Interviews – students can schedule or take interviews, simulate real‑world experience.

💬 Alumni Q&A – students post questions, alumni provide answers/advice.

📊 Progress Dashboard – students track their test results, challenge completions, interview readiness.

🔐 Role‑based Access – distinct views for Students, Alumni, Admin.

📂 Admin Panel – manage users, tests, challenges, content, analytics.

Tech Stack

Backend: Python (Flask) – based on app.py.

Frontend: HTML / CSS / JavaScript (templates folder).

Static Assets: static/images etc.

Environment Management: .env for configuration.

Dependencies: listed in requirements.txt.

Version Control: Git / GitHub.

(Optional future enhancements: DB migrations, API endpoints, React/Vue frontend.)

Getting Started
Prerequisites

Python 3.x installed on your system.

pip (Python package installer) available.

Basic understanding of terminal/command‑line.

(Optional) Virtual environment tool recommended.

Installation

Clone the repository

git clone https://github.com/namitha-maria/campus-career-connect.git  
cd campus-career-connect  


Create and activate a virtual environment (recommended)

python3 -m venv venv  
source venv/bin/activate   # On Windows: venv\Scripts\activate  


Install dependencies

pip install -r requirements.txt  

Configuration

Copy the example environment file

cp .env.example .env  


Open .env and set your configuration variables (e.g., database URL, secret keys, mail settings, etc.)

(Optionally) Set up a database (e.g., SQLite, PostgreSQL) and update your .env accordingly.

Running the App

With the environment set up, run:

python app.py  


Then open your browser and navigate to http://localhost:5000 (or whichever port is configured) to see the app in action.

Usage

Students: Register / login → take tests → complete coding challenges → schedule mock interviews → view progress dashboard.

Alumni: Log in → respond to student questions → optionally schedule interview sessions or host workshops.

Admin: Manage users, content, tests, challenges, monitor usage stats, update site content.

Customization: You can add/edit question banks, challenge sets, interview templates, dashboard widgets as needed.

Project Structure
campus‑career‑connect/
│  
├── app.py                   # Main application entry  
├── requirements.txt         # Python dependencies  
├── .env.example             # Sample environment file  
│  
├── templates/               # HTML templates  
│   ├── …  
│  
├── static/                  # Static assets (images, CSS, JS)  
│   └── images/  
│  
└── … (other modules, blueprints, assets)  


This structure keeps backend logic (app.py), front‑end templates, and static assets separated for clarity and maintainability.

Contributing

We welcome contributions! Please follow these steps:

Fork the repository.

Create a new branch: git checkout -b feature/my‑awesome‑feature.

Make your changes and commit: git commit -m "Add some feature".

Push to your branch: git push origin feature/my‑awesome‑feature.

Open a Pull Request (PR) describing your change.

Please ensure:

Your code is clean and follows existing style.

You test new functionality and it works as expected.

Any new dependencies are documented in requirements.txt.

You update the README if you introduce new user‑facing features.

License

This project is licensed under the MIT License. (You may adapt or replace with your preferred license.)

Contact

For any questions, issues or suggestions:

Author: Namitha Maria (GitHub: namitha‑maria)

Project repository: https://github.com/namitha-maria/campus-career-connect

Feel free to open an issue or discussion for anything related!
