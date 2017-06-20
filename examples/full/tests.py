from django.test import TestCase
# from django.test import Client

# from .models import MyCategory, MyModel


class ShoptoolsTestCase(TestCase):
    def setUp(self):
        pass

    def test_sample(self):
        self.assertEqual(1, 1)

    # def test_search_view(self):
    #     c = Client()
    #
    #     response = c.get('/search?q=beautiful')
    #     self.assertEqual(response.content.decode("utf-8"), 'Line one')
    #
    #     response = c.get('/search?q=complex')
    #     self.assertEqual(response.content.decode("utf-8"),
    #                      'Line two,Line three')
    #
    #     response = c.get('/search?q=line')
    #     self.assertEqual(response.content.decode("utf-8"),
    #                      'Line one,Line two,Line three')
