# 🌸 Emotional Planner

**Emotional Planner** este o aplicație web creată cu Django, care ajută utilizatorii să își organizeze ziua într-un mod blând și conștient, punând accent pe starea emoțională, echilibru și reflecție, nu pe presiune sau productivitate toxică.

👉 Aplicația este gândită ca un *safe space digital* pentru planificarea zilnică.

---

## ✨ Funcționalități

- ✅ Înregistrare cu **email + parolă**
- ✅ Autentificare cu **email + parolă**
- ✅ Logout securizat
- ✅ Pagini protejate (acces doar pentru utilizatori autentificați)
- ✅ Planner zilnic („Today”)
- ✅ Profil utilizator
- ✅ Interfață simplă, aerisită, pastel, orientată spre wellbeing
- ✅ Sistem stabil, fără confirmare email (pentru fiabilitate pe free hosting)

---

## 🛠️ Tehnologii folosite

- **Backend:** Django
- **Frontend:** HTML, CSS
- **Database:** SQLite (local) / PostgreSQL (prod)
- **Auth:** Django built-in authentication (email-based login)
- **Deploy:** Railway
- **Static files:** WhiteNoise
- **Python:** 3.x

---

## 🚀 Demo live

👉 https://dayplanner-production.up.railway.app/

---

## 🔐 Autentificare

- Utilizatorii se înregistrează folosind **email și parolă**
- Emailul este folosit intern ca username
- Nu este necesară confirmarea prin email

---

## ⚙️ Rulare locală

```bash
git clone https://github.com/SanduAndreea22/day_planner.git
cd day_planner
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```


## 👩‍💻 Autor

**Andreea Sandu**  
LinkedIn: https://linkedin.com/in/andreealuizasandu  

✨ *Made with calm & a lot of debugging.* ✨
