# 🌸 Emotional Planner

**Emotional Planner** is a Django web application designed to help users organize their day in a gentle and mindful way. It emphasizes **emotional wellbeing, balance, and reflection**, not pressure or toxic productivity.

👉 The app is a *digital safe space* for your daily planning.

---

## ✨ Features

- ✅ Sign up with **email + password**
- ✅ Login with **email + password**
- ✅ Secure logout
- ✅ Protected pages (accessible only to authenticated users)
- ✅ Daily planner (“Today”)
- ✅ User profile
- ✅ Clean, airy, pastel interface focused on wellbeing
- ✅ Stable system with **no email confirmation required** (works reliably on free hosting)

---

## 🛠️ Technologies Used

| Layer       | Technology                                     |
|------------|-----------------------------------------------|
| Backend     | Django                                        |
| Frontend    | HTML, CSS                                     |
| Database    | SQLite (local) / PostgreSQL (production)     |
| Auth        | Django built-in authentication (email login) |
| Deploy      | Railway                                       |
| Static files| WhiteNoise                                    |
| Python      | 3.x                                           |

---

## 🚀 Live Demo

🌐 [Check out the demo](https://day-planner-e2sv.onrender.com)

---

## 🔐 Authentication

- Users sign up with **email and password**  
- Email is used internally as the username  
- **No email confirmation required**

---
## 👩‍💻 Autor
Andreea Sandu
LinkedIn: https://linkedin.com/in/andreealuizasandu

✨ Made with calm & a lot of debugging. ✨

## ⚙️ Running Locally

```bash
git clone https://github.com/SanduAndreea22/day_planner.git
cd day_planner
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver


