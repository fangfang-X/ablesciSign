import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ablesci


class AbleSciTests(unittest.TestCase):
    def test_csrf_page_variants(self):
        cases = [
            ('<input name="_csrf" value="legacy">', 'legacy'),
            ('<meta name="csrf-token" content="current">', 'current'),
            ('<meta name="csrf-token" content=" current "><input name="_csrf" value="legacy">', 'current'),
            ('<meta name="csrf-token" content=" "><input name="_csrf" value="legacy">', 'legacy'),
            ('<input name="_csrf" value=""><meta name="csrf-token" content="fallback">', 'fallback'),
            ('<html></html>', ''),
        ]
        for html, expected in cases:
            with self.subTest(html=html):
                client = ablesci.AbleSciAuto('test@example.com', 'secret', notifier=Mock())
                client.session.get = Mock(return_value=Mock(status_code=200, text=html))
                self.assertEqual(client.get_csrf_token(), expected)

    def test_account_logs_do_not_expose_credentials(self):
        for value, expected in [
            ('test@example.com:secret-value', [('test@example.com', 'secret-value')]),
            ('secret-value', []),
            (':secret-value', []),
        ]:
            with self.subTest(value=value), patch.dict(os.environ, {'ABLESCI_ACCOUNTS': value}):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    self.assertEqual(ablesci.get_accounts(), expected)
                self.assertNotIn('secret-value', output.getvalue())
                self.assertNotIn('test@example.com', output.getvalue())

    def test_env_file_logs_do_not_expose_credentials(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, '.env').write_text('ABLESCI_ACCOUNTS=test@example.com:secret-value\n', encoding='utf-8')
            with patch.object(ablesci, '__file__', str(Path(directory, 'ablesci.py'))), patch.dict(os.environ, {}, clear=True):
                output = io.StringIO()
                with contextlib.redirect_stdout(output):
                    ablesci.load_env_file()
                self.assertEqual(os.environ['ABLESCI_ACCOUNTS'], 'test@example.com:secret-value')
                self.assertNotIn('secret-value', output.getvalue())


if __name__ == '__main__':
    unittest.main()
