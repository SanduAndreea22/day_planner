from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import UserProfile


# ===================================================
# 🌸 REGISTER FORM — EMAIL + PAROLĂ (SAFE, CU CONFIRMARE EMAIL)
# ===================================================
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Parolă",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Introdu parola",
            "autocomplete": "new-password"
        })
    )

    password2 = forms.CharField(
        label="Confirmă parola",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirmă parola",
            "autocomplete": "new-password"
        })
    )

    class Meta:
        model = User
        fields = ["email"]
        labels = {"email": "Adresa de email"}
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Adresa de email"})
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("Acest email este deja folosit 💭")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2:
            if p1 != p2:
                raise ValidationError("Parolele nu coincid, mai încearcă 🤍")
            validate_password(p1)

        return cleaned_data

    def save(self, commit=True):
        """
        ✅ Creează user inactiv (până confirmă emailul)
        ✅ Generează username unic automat
        """
        user = super().save(commit=False)
        email = self.cleaned_data["email"].lower()
        user.username = f"user_{User.objects.count() + 1}"
        user.email = email
        user.set_password(self.cleaned_data["password1"])

        # Dezactivat până la confirmarea email-ului
        user.is_active = False

        if commit:
            user.save()
        return user


# ===================================================
# 🔑 LOGIN FORM — AUTENTIFICARE CU EMAIL
# ===================================================
class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Adresa de email"})
    )
    password = forms.CharField(
        label="Parolă",
        widget=forms.PasswordInput(attrs={"placeholder": "Introdu parola"})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").lower()
        password = cleaned_data.get("password")

        if not email or not password:
            raise ValidationError("Te rugăm să completezi email-ul și parola 💭")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("Email sau parolă incorectă 💭")

        user = authenticate(username=user.username, password=password)

        if user is None:
            raise ValidationError("Email sau parolă incorectă 💭")

        if not user.is_active:
            raise ValidationError("Contul nu este activ. Te rugăm să confirmi email-ul 💌")

        self.user = user
        return cleaned_data

    def get_user(self):
        return self.user


# ===================================================
# 👤 PROFILE FORM — DATE PERSONALE
# ===================================================
class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["nickname", "bio"]

        labels = {
            "nickname": "Cum vrei să te strig?",
            "bio": "Câteva cuvinte despre tine",
        }

        help_texts = {
            "nickname": "Poate fi un nume real, un diminutiv sau un nickname.",
            "bio": "Nu trebuie să fie complet. Poate fi chiar o propoziție.",
        }

        widgets = {
            "nickname": forms.TextInput(attrs={
                "maxlength": 20,
                "placeholder": "Andi",
            }),
            "bio": forms.Textarea(attrs={
                "rows": 4,
                "maxlength": 200,
                "placeholder": "Cum te simți în perioada asta?"
            }),
        }
