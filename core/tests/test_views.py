from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from core.models import Pet, Match, Message


class ViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.pet = Pet.objects.create(owner=self.user, name='Test Pet', species='Dog', age=2, gender='male')

    def test_landing_view(self):
        response = self.client.get(reverse('landing'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'PawMate')

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('dashboard')}")

    def test_dashboard_authenticated(self):
        self.client.login(username='testuser', password='password')
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_healthz(self):
        response = self.client.get(reverse('healthz'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('ok', response.json())

    def test_swipe_requires_login(self):
        response = self.client.get(reverse('swipe'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('swipe')}")

    def test_pet_create_requires_login(self):
        response = self.client.get(reverse('pet_create'))
        self.assertRedirects(response, f"{reverse('login')}?next={reverse('pet_create')}")

    def test_register_view(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_login_view(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)