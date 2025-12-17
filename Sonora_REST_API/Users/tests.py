from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class DeleteUserByEmailTestCase(APITestCase):
    def setUp(self):
        # Create a test user
        self.test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.url = reverse('delete_user_by_email')

    def test_delete_existing_user(self):
        """Test deleting an existing user by email"""
        response = self.client.delete(f'{self.url}?email=test@example.com')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('has been deleted successfully',
                      response.data['message'])

        # Verify user is deleted
        with self.assertRaises(User.DoesNotExist):
            User.objects.get(email='test@example.com')

    def test_delete_nonexistent_user(self):
        """Test attempting to delete a user that doesn't exist"""
        response = self.client.delete(
            f'{self.url}?email=nonexistent@example.com')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('not found', response.data['error'])

    def test_delete_without_email_parameter(self):
        """Test attempting to delete without providing email parameter"""
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Email parameter is required', response.data['error'])
