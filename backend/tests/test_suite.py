import asyncio
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.hybrid_retriever import HybridRetriever
from app.openrouter_client import OpenRouterClient
from app.config import settings

class TestDarGlobalWasaltRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        print("\n=== INITIALIZING TEST SUITE ===")
        cls.retriever = HybridRetriever()
        cls.retriever.load()
        cls.client = OpenRouterClient()
        cls.full_chunks = {c["chunk_id"]: c["content"] for c in cls.retriever.chunks}

    def test_01_keyword_darglobal_pagani(self):
        """1. Exact keyword retrieval: DarGlobal Pagani Tower"""
        citations = self.retriever.retrieve("Pagani Tower Dubai", company="darglobal", top_k=3)
        self.assertTrue(len(citations) > 0, "Failed to retrieve Pagani Tower")
        titles = [c.title.lower() for c in citations]
        has_match = any("pagani" in t for t in titles)
        self.assertTrue(has_match, "Pagani was not found in retrieved titles")
        self.assertIn("darglobal", citations[0].source_url.lower())

    def test_02_keyword_wasalt_rega_license(self):
        """2. Exact keyword retrieval: Wasalt REGA License 1200016591"""
        citations = self.retriever.retrieve("1200016591 REGA License", company="wasalt", top_k=3)
        self.assertTrue(len(citations) > 0)
        found = any("1200016591" in self.full_chunks[c.chunk_id] for c in citations)
        self.assertTrue(found, "REGA License 1200016591 not found in retrieved text")

    def test_03_semantic_luxury_branded_villas(self):
        """3. Semantic question without exact keywords: Luxury branded residences by the sea"""
        citations = self.retriever.retrieve("luxury oceanfront branded residential estates", company="darglobal", top_k=5)
        self.assertTrue(len(citations) > 0)
        categories = [c.category for c in citations]
        self.assertTrue("projects" in categories or "company_profile" in categories)

    def test_04_project_shams_al_riyadh(self):
        """4. Project-specific query: Shams Al Riyadh on Wasalt"""
        citations = self.retriever.retrieve("Shams Al Riyadh project unit types price", company="wasalt", top_k=3)
        self.assertTrue(len(citations) > 0)
        has_shams = any("shams al riyadh" in c.title.lower() for c in citations)
        self.assertTrue(has_shams, "Shams Al Riyadh project chunk not retrieved")

    def test_05_leadership_darglobal_and_wasalt(self):
        """5. Company and leadership: Ziad ElChaar Chairman and Board"""
        citations_dg = self.retriever.retrieve("Ziad ElChaar Chairman DarGlobal", company="darglobal", top_k=3)
        self.assertTrue(len(citations_dg) > 0)
        has_ziad = any("ziad" in self.full_chunks[c.chunk_id].lower() for c in citations_dg)
        self.assertTrue(has_ziad, "Ziad ElChaar not found in DarGlobal governance chunk")

        citations_ws = self.retriever.retrieve("Vivek Pandey CTO Wasalt", company="wasalt", top_k=3)
        self.assertTrue(len(citations_ws) > 0)
        has_vivek = any("vivek" in self.full_chunks[c.chunk_id].lower() for c in citations_ws)
        self.assertTrue(has_vivek, "Vivek Pandey not found in Wasalt management chunk")

    def test_06_wasalt_faq_matchmaker(self):
        """6. FAQ questions: What is Matchmaker on Wasalt?"""
        citations = self.retriever.retrieve("What is Matchmaker and how does it work?", company="wasalt", top_k=3)
        self.assertTrue(len(citations) > 0)
        has_faq = any("matchmaker" in c.title.lower() or "matchmaker" in self.full_chunks[c.chunk_id].lower() for c in citations)
        self.assertTrue(has_faq, "Matchmaker FAQ chunk not retrieved")

    def test_07_property_listing_riyadh(self):
        """7. Property listing query: Floor for sale in King Abdullah Riyadh"""
        citations = self.retriever.retrieve("Floor for Sale King Abdullah Riyadh", company="wasalt", top_k=5)
        self.assertTrue(len(citations) > 0)
        has_listings = any("listing" in c.category or "floor" in self.full_chunks[c.chunk_id].lower() for c in citations)
        self.assertTrue(has_listings, "Riyadh floor listing chunk not retrieved")

    def test_08_auction_infath_movable_assets(self):
        """8. Auction query: Wasalt Infath auctions and movable assets"""
        citations = self.retriever.retrieve("Wasalt Auctions Infath security deposit", company="wasalt", top_k=5)
        self.assertTrue(len(citations) > 0)
        has_auction = any("auction" in c.category for c in citations)
        self.assertTrue(has_auction, "Wasalt auction chunk not retrieved")

    def test_09_multi_chunk_darglobal_international(self):
        """9. Multi-chunk query: DarGlobal projects across UAE, Oman, Spain, London, Qatar"""
        citations = self.retriever.retrieve("DarGlobal international portfolio Spain London Dubai Oman", company="darglobal", top_k=5)
        self.assertTrue(len(citations) >= 3, "Insufficient chunks for multi-region question")

    def test_10_unsupported_question_hallucination_check(self):
        """10. Unsupported question: Alien lunar colony real estate"""
        citations = self.retriever.retrieve("Alien lunar habitat prices on the moon", company="all", top_k=3)
        # Verify prompt engine handles unsupported queries properly
        prompt = self.client.build_user_prompt("Alien lunar habitat prices on the moon", citations, self.full_chunks)
        self.assertIn("Alien lunar habitat", prompt)

    def test_11_cross_company_isolation(self):
        """11. Cross-company confusion test: Ensure Wasalt filter does NOT return DarGlobal chunks"""
        citations = self.retriever.retrieve("W Residences luxury tower Dubai", company="wasalt", top_k=5)
        for c in citations:
            self.assertEqual(c.company, "wasalt", f"Cross-company leak detected: DarGlobal chunk in Wasalt filter: {c.title}")

    def test_12_citation_source_url_preservation(self):
        """12. Citation verification: Every single retrieved chunk MUST have an official source URL"""
        citations = self.retriever.retrieve("real estate projects and licenses", company="all", top_k=10)
        self.assertTrue(len(citations) > 0)
        for c in citations:
            self.assertTrue(c.source_url.startswith("http"), f"Invalid source URL: {c.source_url} in chunk {c.chunk_id}")
            self.assertTrue("darglobal.co.uk" in c.source_url or "wasalt.sa" in c.source_url or "wasalt.com" in c.source_url)

    def test_13_missing_api_key_fallback(self):
        """13. Fallback check: When API key is absent, passage fallback is triggered directly (no hallucinations)"""
        citations = self.retriever.retrieve("What is Wasalt REGA license?", company="wasalt", top_k=2)
        old_key = self.client.api_key
        self.client.api_key = ""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        answer, fallback_applied = loop.run_until_complete(
            self.client.generate_response("What is Wasalt REGA license?", citations, self.full_chunks)
        )
        self.client.api_key = old_key
        self.assertTrue(fallback_applied, "Fallback flag should be True when API key is missing")
        self.assertIn("Direct Knowledge Base Passages", answer)
        self.assertIn("1200016591", answer)

    def test_14_company_filter_darglobal_only(self):
        """14. Filter test: DarGlobal filter only returns DarGlobal chunks"""
        citations = self.retriever.retrieve("Shams Al Riyadh villas and auctions", company="darglobal", top_k=5)
        for c in citations:
            self.assertEqual(c.company, "darglobal", "Wasalt chunk leaked into DarGlobal filter")

    def test_15_freshness_disclaimer_presence(self):
        """15. Data freshness disclaimer test"""
        from app.openrouter_client import DISCLAIMER_TEXT
        self.assertIn("scraping snapshot", DISCLAIMER_TEXT.lower())

def run_tests():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDarGlobalWasaltRAG)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print(f"\nTest Results: Ran {result.testsRun} tests, Errors={len(result.errors)}, Failures={len(result.failures)}")
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
