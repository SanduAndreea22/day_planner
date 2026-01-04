from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import UserProfile


# ===================================================
# 🌸 REGISTER FORM — EMAIL + PASSWORD (SAFE, WITH EMAIL CONFIRMATION)
# ===================================================
class RegisterForm(forms.ModelForm):
    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter your password",
            "autocomplete": "new-password"
        })
    )

    password2 = forms.CharField(
        label="Confirm Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Confirm your password",
            "autocomplete": "new-password"
        })
    )

    class Meta:
        model = User
        fields = ["email"]
        labels = {"email": "Email address"}
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "Email address"})
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already in use 💭")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2:
            if p1 != p2:
                raise ValidationError("Passwords do not match, please try again 🤍")
            validate_password(p1)

        return cleaned_data

    def save(self, commit=True):
        """
        ✅ Creates an inactive user (until email is confirmed)
        ✅ Generates a unique username automatically
        """
        user = super().save(commit=False)
        email = self.cleaned_data["email"].lower()
        user.username = f"user_{User.objects.count() + 1}"
        user.email = email
        user.set_password(self.cleaned_data["password1"])

        # Inactive until email confirmation
        user.is_active = False

        if commit:
            user.save()
        return user


# ===================================================
# 🔑 LOGIN FORM — AUTHENTICATION WITH EMAIL
# ===================================================
class EmailAuthenticationForm(forms.Form):
    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "Email address"})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"placeholder": "Enter your password"})
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("email", "").lower()
        password = cleaned_data.get("password")

        if not email or not password:
            raise ValidationError("Please fill in both email and password 💭")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("Incorrect email or password 💭")

        user = authenticate(username=user.username, password=password)

        if user is None:
            raise ValidationError("Incorrect email or password 💭")

        if not user.is_active:
            raise ValidationError("Account is inactive. Please confirm your email 💌")

        self.user = user
        return cleaned_data

    def get_user(self):
        return self.user


# ===================================================
# 👤 PROFILE FORM — PERSONAL DATA
# ===================================================
class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["nickname", "bio"]

        labels = {
            "nickname": "What should we call you?",
            "bio": "A few words about yourself",
        }

        help_texts = {
            "nickname": "Can be your real name, a nickname, or a handle.",
            "bio": "Doesn't need to be complete. Can be just one sentence.",
        }

        widgets = {
            "nickname": forms.TextInput(attrs={
                "maxlength": 20,
                "placeholder": "Andi",
            }),
            "bio": forms.Textarea(attrs={
                "rows": 4,
                "maxlength": 200,
                "placeholder": "How have you been feeling lately?"
            }),
        }
