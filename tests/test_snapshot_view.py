import unittest
from atlas.snapshot_view import snapshot_page


class SnapshotViewTests(unittest.TestCase):
    def test_readable_evidence_does_not_run_or_load_source_content(self):
        row=dict(id='saved-id',source='federal',retrieved_at='2026-09-28T10:00:00Z',
                 raw_html='''<html><head><script>HEAD_ATTACK</script></head><body><main>
                 <h1 onclick="ATTACK()">Current rate</h1><p>12.85 AST &amp; coverage</p>
                 <script>BODY_ATTACK</script><iframe src="https://bad.example"></iframe>
                 <img src="https://bad.example/pixel"><p hidden>HIDDEN</p>
                 <details><summary>Notice details</summary><p>Effective September 28</p></details>
                 </main></body></html>''')
        result=snapshot_page(row,'live')
        self.assertIn('<h1>Current rate</h1>',result)
        self.assertIn('12.85 AST &amp; coverage',result)
        self.assertIn('<summary>Notice details</summary>',result)
        self.assertIn('format=raw',result)
        self.assertIn('2026-09-28T10:00:00Z',result)
        for forbidden in ('ATTACK','bad.example','HIDDEN','onclick','<script','<iframe','<img'):
            self.assertNotIn(forbidden,result)
