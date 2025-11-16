from django.test import TestCase
from users.models import User, AuthProvider


class UserModelTest(TestCase):
    def test_create_user(self):
        """Test creating a new user"""
        user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            password='testpass123',
            is_active=True
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.name, 'Test User')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(str(user), 'test@example.com')

    def test_create_superuser(self):
        """Test creating a new superuser"""
        admin_user = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(admin_user.email, 'admin@example.com')
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)

    def test_create_user_without_email_raises_error(self):
        """Test that creating a user without an email raises an error"""
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='testpass123')


class AuthProviderModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )

    def test_create_auth_provider(self):
        """Test creating an auth provider for a user"""
        auth_provider = AuthProvider.objects.create(
            user=self.user,
            provider=AuthProvider.Choices.GOOGLE,
            provider_id='google123'
        )
        self.assertEqual(auth_provider.user, self.user)
        self.assertEqual(auth_provider.provider, 'google')
        self.assertEqual(auth_provider.provider_id, 'google123')
        self.assertEqual(
            str(auth_provider),
            f"{auth_provider.provider} account for {self.user.email}"
        )

    def test_unique_together_constraint(self):
        """Test that provider and provider_id must be unique together"""
        AuthProvider.objects.create(
            user=self.user,
            provider=AuthProvider.Choices.GOOGLE,
            provider_id='google123'
        )
        with self.assertRaises(Exception):
            AuthProvider.objects.create(
                user=self.user,
                provider=AuthProvider.Choices.GOOGLE,
                provider_id='google123'
            )

