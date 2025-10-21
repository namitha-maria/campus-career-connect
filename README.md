# 🎓 Campus Career Connect

A comprehensive platform connecting students with alumni for career guidance and career preparation — including aptitude tests, coding challenges, mock interviews, and a Q&A forum.

---

## 📚 Table of Contents

- [About](#about)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the App](#running-the-app)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 🧠 About

Campus Career Connect is a web application that bridges the gap between students and alumni. It helps students:

- Prepare for interviews and placements
- Take aptitude and coding tests
- Ask career-related questions to alumni
- Track progress through a student dashboard

This project is ideal for college career cells or tech communities looking to organize and scale mentorship and skill development.

---

## ✨ Features

- 📝 **Aptitude Tests** – Quantitative, logical, and verbal MCQs
- 💻 **Coding Challenges** – Practice and evaluation
- 🎤 **Mock Interviews** – Interview simulations
- 💬 **Alumni Q&A Forum** – Guidance directly from alumni
- 📊 **Progress Dashboard** – Visual insights for students
- 🔐 **Role-Based Access** – Student, Alumni, Admin
- 🧑‍💼 **Admin Panel** – Manage users, content, and platform

---

## 🛠️ Tech Stack

- **Backend:** Python (Flask)
- **Frontend:** HTML, CSS, JavaScript
- **Templating Engine:** Jinja2 (Flask templates)
- **Static Assets:** Stored in `/static`
- **Version Control:** Git & GitHub

---

## 🚀 Getting Started

### ✅ Prerequisites

- Python 3.x
- `pip` package manager
- (Optional) Virtual environment tool (like `venv`)

### 📦 Installation

```bash
# Clone the repository
git clone https://github.com/namitha-maria/campus-career-connect.git
cd campus-career-connect

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### ⚙️ Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Update the `.env` file with your values (e.g., database URI, secret key)

### ▶️ Running the App

```bash
python app.py
```

Then visit: [http://localhost:5000](http://localhost:5000)

---

## 🧪 Usage

- **Students**: Register → Take tests → Attend interviews → Ask questions
- **Alumni**: Login → View questions → Post responses → Conduct interviews
- **Admins**: Manage content, users, and analytics from dashboard

---

## 🗂️ Project Structure

```
campus-career-connect/
│
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── .env.example            # Environment config sample
│
├── templates/              # HTML templates (Jinja2)
│   └── *.html
│
├── static/                 # Static assets (CSS, JS, images)
│   └── images/
│
└── ... (additional modules)
```

---

## 🤝 Contributing

Contributions are welcome!

```bash
# 1. Fork the repo
# 2. Create a new branch
git checkout -b feature/your-feature-name

# 3. Make changes and commit
git commit -m "Add your message"

# 4. Push and open a pull request
git push origin feature/your-feature-name
```

Please ensure your changes are clean, tested, and documented.

---

## 📄 License

This project is licensed under the **MIT License**.  
You are free to use, modify, and distribute with attribution.

---

## 📬 Contact

**Author:** [Namitha Maria](https://github.com/namitha-maria)  
**GitHub Repo:** [Campus Career Connect](https://github.com/namitha-maria/campus-career-connect)

If you find this project useful, give it a ⭐ on GitHub!

