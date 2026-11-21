import os
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Profile

ALLOWED_AVATAR_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}
MAX_AVATAR_SIZE = 2 * 1024 * 1024  # 2 МБ


def validate_avatar_file(avatar):
    if not avatar:
        return avatar
    ext = os.path.splitext(avatar.name)[1].lower()
    if ext not in ALLOWED_AVATAR_EXTENSIONS:
        raise ValidationError('Допустимые форматы аватара: JPG, PNG, WebP.')
    if avatar.size > MAX_AVATAR_SIZE:
        raise ValidationError('Размер файла не должен превышать 2 МБ.')
    return avatar


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=64,
        label='Логин',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваш логин'}),
    )
    password = forms.CharField(
        max_length=64,
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••••'}),
    )

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username')
        password = cleaned_data.get('password')

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)
            if self.user_cache is None:
                raise ValidationError('Неверный логин или пароль. Проверьте раскладку и попробуйте снова.')
        return cleaned_data

    def get_user(self):
        return self.user_cache


class SignupForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        max_length=100,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'user@example.com'}),
    )
    nickname = forms.CharField(
        max_length=50,
        required=True,
        label='Отображаемое имя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Как вас будут видеть другие участники'}),
    )
    password = forms.CharField(
        max_length=64,
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Минимум 8 символов'}),
    )
    password_confirm = forms.CharField(
        max_length=64,
        label='Повторите пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Повторите введенный пароль'}),
    )
    avatar = forms.ImageField(
        required=False,
        label='Аватар',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/png, image/jpeg, image/webp'}),
    )

    class Meta:
        model = User
        fields = ('username', 'email')
        labels = {'username': 'Логин'}
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'maxlength': 32}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('Пользователь с таким email уже зарегистрирован.')
        return email

    def clean_avatar(self):
        return validate_avatar_file(self.cleaned_data.get('avatar'))

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Введенные пароли не совпадают.')

        if password:
            temp_user = User(
                username=cleaned_data.get('username', ''),
                email=cleaned_data.get('email', ''),
            )
            try:
                validate_password(password, user=temp_user)
            except ValidationError as exc:
                self.add_error('password', exc)

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            Profile.objects.create(
                user=user,
                nickname=self.cleaned_data['nickname'].strip(),
                avatar=self.cleaned_data.get('avatar'),
            )
        return user


class ProfileForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        max_length=100,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
    )
    nickname = forms.CharField(
        required=True,
        max_length=50,
        label='Никнейм',
        widget=forms.TextInput(attrs={'class': 'form-control'}),
    )
    avatar = forms.ImageField(
        required=False,
        label='Аватар',
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/png, image/jpeg, image/webp'}),
    )

    class Meta:
        model = Profile
        fields = ('nickname', 'avatar')

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['email'].initial = user.email
            if not self.initial.get('nickname'):
                self.fields['nickname'].initial = user.username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError('Этот email уже занят другим пользователем.')
        return email

    def clean_avatar(self):
        return validate_avatar_file(self.cleaned_data.get('avatar'))

    def save(self, commit=True):
        profile = super().save(commit=False)
        self.user.email = self.cleaned_data['email']
        if commit:
            self.user.save(update_fields=['email'])
            profile.save()
        return profile