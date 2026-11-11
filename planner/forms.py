import uuid

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile, TimeBlock, Feedback

class RegisterForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)

    password1 = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter your password",
            "autocomplete": "new-password"
        })
    )

    password2 = forms.CharField(
        label="Confirm password",
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
            "email": forms.EmailInput(attrs={"placeholder": "name@example.com"})
        }
        error_messages = {
            "email": {"invalid": "That doesn’t look like an email address."},
        }

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise ValidationError("An account with this email already exists. Try logging in instead.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")

        if p1 and p2:
            if p1 != p2:
                raise ValidationError("The two passwords don’t match. Please try again.")
            validate_password(p1)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        email = self.cleaned_data["email"].lower()
        # A random suffix instead of a sequential count avoids a race
        # condition where two concurrent sign-ups compute the same username
        # and one fails with an uncaught IntegrityError.
        user.username = f"user_{uuid.uuid4().hex[:12]}"
        user.email = email
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

class EmailAuthenticationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)

    email = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"placeholder": "name@example.com"}),
        error_messages={"invalid": "That doesn’t look like an email address."},
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
            raise ValidationError("Enter both your email and your password.")

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise ValidationError("Incorrect email or password.")

        user = authenticate(username=user.username, password=password)

        if user is None:
            raise ValidationError("Incorrect email or password.")

        self.user = user
        return cleaned_data

    def get_user(self):
        return self.user

class ProfileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("label_suffix", "")
        super().__init__(*args, **kwargs)

    class Meta:
        model = UserProfile
        fields = ["nickname", "bio"]

        labels = {
            "nickname": "What should the app call you?",
            "bio": "About you",
        }

        help_texts = {
            "nickname": "Can be your real name, a nickname, or a handle.",
            "bio": "Optional. A sentence is enough. Only you see this.",
        }

        widgets = {
            "nickname": forms.TextInput(attrs={
                "id": "nickname",
                "class": "profile-input",
                "maxlength": 20,
                "placeholder": "Alex",
            }),
            "bio": forms.Textarea(attrs={
                "id": "bio",
                "class": "profile-textarea",
                "rows": 4,
                "maxlength": 200,
                "placeholder": "A sentence about you, or leave it blank."
            }),
        }

class TimeBlockForm(forms.ModelForm):
    class Meta:
        model = TimeBlock
        fields = ["title", "start_time", "end_time"]

class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ["message"]
        labels = {"message": "Your message"}
        widgets = {
            "message": forms.Textarea(attrs={
                "rows": 5,
                "maxlength": 1000,
                "placeholder": "Write anything: a bug, an idea, something confusing…",
            })
        }
