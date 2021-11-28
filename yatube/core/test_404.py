from django.test import TestCase, Client


class CoreTests(TestCase):

    def setUp(self):
        self.guest = Client()

    def test_page_not_found(self):
        """Возврат кода 404, если страница не найдена; кастомный шаблон"""
        response = self.guest.get('/nonexisting_page/')
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, 'core/404.html')
