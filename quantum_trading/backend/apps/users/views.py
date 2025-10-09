# apps/users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, UpdateView, FormView
from django.contrib.auth import login, authenticate
from django.urls import reverse_lazy
from django.contrib import messages

from .forms import CustomUserCreationForm, UserProfileForm
from .models import CustomUser, UserProfile

class RegisterView(FormView):
    """
    User registration view
    """
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Account created successfully!')
        return super().form_valid(form)

class ProfileView(LoginRequiredMixin, UpdateView):
    """
    User profile management
    """
    model = CustomUser
    template_name = 'users/profile.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('profile')

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = getattr(self.request.user, 'profile', None)
        return context

class TradingPreferencesView(LoginRequiredMixin, TemplateView):
    """
    Trading preferences and risk management settings
    """
    template_name = 'users/trading_preferences.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context.update({
            'risk_profiles': CustomUser.RISK_PROFILE_CHOICES,
            'user_profile': getattr(user, 'profile', None)
        })
        return context