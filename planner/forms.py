import uuid

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import UserProfile, TimeBlock, Feedback

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

        self.user = user
        return cleaned_data

    def get_user(self):
        return self.user

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ["nickname", "bio", "evening_reminder_time"]

        labels = {
            "nickname": "What should we call you?",
            "bio": "A few words about yourself",
            "evening_reminder_time": "Evening reminder",
        }

        help_texts = {
            "nickname": "Can be your real name, a nickname, or a handle.",
            "bio": "Doesn't need to be complete. Can be just one sentence.",
            "evening_reminder_time": "Optional. We'll email you around this time if you haven't closed the day yet.",
        }

        widgets = {
            "nickname": forms.TextInput(attrs={
                "id": "nickname",
                "class": "profile-input",
                "maxlength": 20,
                "placeholder": "Andi",
            }),
            "bio": forms.Textarea(attrs={
                "id": "bio",
                "class": "profile-textarea",
                "rows": 4,
                "maxlength": 200,
                "placeholder": "How have you been feeling lately?"
            }),
            "evening_reminder_time": forms.TimeInput(attrs={
                "id": "evening_reminder_time",
                "class": "profile-input",
                "type": "time",
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
        labels = {"message": "What's on your mind?"}
        widgets = {
            "message": forms.Textarea(attrs={
                "rows": 5,
                "maxlength": 1000,
                "placeholder": "Tell us what's working, what's missing, or what felt off...",
            })
        }
