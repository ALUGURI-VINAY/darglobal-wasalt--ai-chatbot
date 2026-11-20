import os
import re
from typing import List, Dict, Any

class StructureAwareChunker:
    """
    Structure-aware recursive markdown chunker.
    Target chunk size: 500-700 tokens (~2000-2800 characters) with 80-100 token overlap (~350-400 characters).
    Preserves record boundaries (projects, auctions, listings, FAQs, press releases, leadership).
    Splits oversized records with overlap without losing metadata or source URLs.
    """
    def __init__(self, target_chars: int = 2400, overlap_chars: int = 350):
        self.target_chars = target_chars
        self.overlap_chars = overlap_chars

    def _extract_url(self, text: str, default_url: str) -> str:
        m = re.search(r'\[(?:View [^\]]+|https?://[^\]]+)\]\((https?://[^\)]+)\)', text)
        if m:
            return m.group(1)
        m2 = re.search(r'(https?://[^\s\)\]]+)', text)
        if m2:
            return m2.group(1)
        return default_url

    def chunk_darglobal(self, markdown_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(markdown_path):
            return []
        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = []
        default_url = "https://darglobal.co.uk"

        sections = re.split(r'\n(?=## )', content)
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            sec_header_match = re.match(r'## (.*?)\n', sec)
            sec_header = sec_header_match.group(1).strip() if sec_header_match else "General"
            sec_url_match = re.search(r'\*\*Source URL\*\*: \[([^\]]+)\]\((https?://[^\)]+)\)', sec)
            sec_url = sec_url_match.group(2) if sec_url_match else default_url

            if "1. Company Information" in sec_header:
                sub_parts = re.split(r'\n(?=### )', sec)
                for part in sub_parts:
                    part = part.strip()
                    if not part:
                        continue
                    if part.startswith("## "):
                        chunks.extend(self._split_record("darglobal", "company_profile", "Company Overview & Stock Listing", part, "DARGLOBAL_VERIFIED_DATA.md", sec_url))
                    elif "Board of Directors" in part:
                        chunks.extend(self._split_record("darglobal", "governance", "Board of Directors", part, "DARGLOBAL_VERIFIED_DATA.md", "https://darglobal.co.uk/investor"))
                    elif "Executive Leadership" in part:
                        chunks.extend(self._split_record("darglobal", "governance", "Executive Leadership", part, "DARGLOBAL_VERIFIED_DATA.md", "https://darglobal.co.uk/about"))
                    else:
                        m_t = re.match(r'### (.*?)\n', part)
                        t = m_t.group(1).strip() if m_t else "Company Information"
                        chunks.extend(self._split_record("darglobal", "company_profile", t, part, "DARGLOBAL_VERIFIED_DATA.md", sec_url))

            elif "2. Brand Collaborations" in sec_header:
                chunks.extend(self._split_record("darglobal", "brand_partners", "Brand Collaborations & Luxury Partners", sec, "DARGLOBAL_VERIFIED_DATA.md", "https://darglobal.co.uk/"))

            elif "3. Real Estate Developments Directory" in sec_header:
                lines = sec.split("\n")
                data_rows = [l for l in lines if l.startswith("|") and not (l.startswith("| Project Title") or l.startswith("|---"))]
                for row in data_rows:
                    cols = [c.strip() for c in row.split("|")[1:-1]]
                    if not cols or not cols[0]:
                        continue
                    title = cols[0].replace("**", "")
                    row_url = self._extract_url(row, "https://darglobal.co.uk/projects")
                    chunk_text = (
                        f"## DarGlobal Project: {title}\n"
                        f"- **Project Title**: {title}\n"
                        f"- **Country**: {cols[1] if len(cols) > 1 else 'N/A'}\n"
                        f"- **Location**: {cols[2] if len(cols) > 2 else 'N/A'}\n"
                        f"- **Project Type**: {cols[3] if len(cols) > 3 else 'N/A'}\n"
                        f"- **Bedrooms**: {cols[4] if len(cols) > 4 else 'N/A'}\n"
                        f"- **Completion Date**: {cols[5] if len(cols) > 5 else 'N/A'}\n"
                        f"- **Official Project Link**: {row_url}\n"
                        f"- **Source URL**: https://darglobal.co.uk/projects\n"
                    )
                    chunks.append({
                        "chunk_id": "",
                        "company": "darglobal",
                        "category": "projects",
                        "title": f"DarGlobal Project: {title}",
                        "content": chunk_text,
                        "source_file": "DARGLOBAL_VERIFIED_DATA.md",
                        "source_url": row_url
                    })

            elif "4. One-of-One Collection" in sec_header:
                lines = sec.split("\n")
                data_rows = [l for l in lines if l.startswith("|") and not (l.startswith("| Property Title") or l.startswith("|---"))]
                for row in data_rows:
                    cols = [c.strip() for c in row.split("|")[1:-1]]
                    if not cols or not cols[0]:
                        continue
                    title = cols[0].replace("**", "")
                    row_url = self._extract_url(row, "https://darglobal.co.uk/one-of-one")
                    chunk_text = (
                        f"## DarGlobal One-of-One Collection: {title}\n"
                        f"- **Property Title**: {title}\n"
                        f"- **Location**: {cols[1] if len(cols) > 1 else 'N/A'}\n"
                        f"- **Property Type**: {cols[2] if len(cols) > 2 else 'N/A'}\n"
                        f"- **Price**: {cols[3] if len(cols) > 3 else 'N/A'}\n"
                        f"- **Status / Highlights**: {cols[4] if len(cols) > 4 else 'N/A'}\n"
                        f"- **Official Link**: {row_url}\n"
                        f"- **Source URL**: https://darglobal.co.uk/one-of-one\n"
                    )
                    chunks.append({
                        "chunk_id": "",
                        "company": "darglobal",
                        "category": "projects",
                        "title": f"DarGlobal One-of-One: {title}",
                        "content": chunk_text,
                        "source_file": "DARGLOBAL_VERIFIED_DATA.md",
                        "source_url": row_url
                    })

            elif "5. Sales Offices" in sec_header:
                chunks.extend(self._split_record("darglobal", "contact", "Sales Offices & Departmental Directory", sec, "DARGLOBAL_VERIFIED_DATA.md", "https://darglobal.co.uk/get-in-touch"))

            elif "6. Official Press Releases" in sec_header:
                sub_records = re.split(r'\n(?=### \[)', sec)
                for sub in sub_records:
                    sub = sub.strip()
                    if not sub or sub.startswith("## "):
                        continue
                    m_title = re.match(r'### \[\d{4}-\d{2}-\d{2}\] (.*?)\n', sub)
                    title = m_title.group(1).strip() if m_title else "DarGlobal Press Release"
                    rec_url = self._extract_url(sub, "https://darglobal.co.uk/press")
                    chunks.extend(self._split_record("darglobal", "press_releases", f"Press Release: {title}", sub, "DARGLOBAL_VERIFIED_DATA.md", rec_url))

            else:
                chunks.extend(self._split_record("darglobal", "company_profile", sec_header, sec, "DARGLOBAL_VERIFIED_DATA.md", sec_url))

        # Re-index chunk IDs cleanly
        for i, c in enumerate(chunks):
            c["chunk_id"] = f"dg_{c['category']}_{i+1:03d}"
        return chunks

    def chunk_wasalt(self, markdown_path: str) -> List[Dict[str, Any]]:
        if not os.path.exists(markdown_path):
            return []
        with open(markdown_path, "r", encoding="utf-8") as f:
            content = f.read()

        chunks = []
        default_url = "https://wasalt.sa/en"

        sections = re.split(r'\n(?=## )', content)
        for sec in sections:
            sec = sec.strip()
            if not sec:
                continue

            sec_header_match = re.match(r'## (.*?)\n', sec)
            sec_header = sec_header_match.group(1).strip() if sec_header_match else "General"
            sec_url_match = re.search(r'\*\*Source URL(?:s)?\*\*: \[([^\]]+)\]\((https?://[^\)]+)\)', sec)
            sec_url = sec_url_match.group(2) if sec_url_match else default_url

            if "Masterplans" in sec_header or "Projects" in sec_header:
                sub_records = re.split(r'\n(?=### Project:)', sec)
                for sub in sub_records:
                    sub = sub.strip()
                    if not sub or sub.startswith("## "):
                        continue
                    m_title = re.match(r'### Project: (.*?)\n', sub)
                    title = m_title.group(1).strip() if m_title else "Wasalt Masterplan Project"
                    rec_url = self._extract_url(sub, sec_url)
                    chunks.extend(self._split_record("wasalt", "projects", title, sub, "WASALT_VERIFIED_DATA.md", rec_url))

            elif "Auctions" in sec_header:
                # Keep table header and split rows or manageable record blocks
                lines = sec.split("\n")
                header_lines = []
                data_rows = []
                for line in lines:
                    if line.startswith("| Auction ID") or line.startswith("| :---"):
                        header_lines.append(line)
                    elif line.startswith("|") and not line.startswith("| Auction ID"):
                        data_rows.append(line)

                if data_rows and header_lines:
                    # Group auctions by 3-4 rows per chunk to keep complete records
                    step = 3
                    for idx in range(0, len(data_rows), step):
                        group = data_rows[idx:idx+step]
                        chunk_text = "## Wasalt Auctions\n**Source URL**: https://auction.wasalt.sa/en\n\n" + "\n".join(header_lines) + "\n" + "\n".join(group)
                        m_aid = re.search(r'\| (\d+) \| (.*?) \|', group[0])
                        title = f"Wasalt Auctions (Group {m_aid.group(2) if m_aid else idx+1})"
                        rec_url = self._extract_url(group[0], "https://auction.wasalt.sa/en")
                        chunks.append({
                            "chunk_id": "",
                            "company": "wasalt",
                            "category": "auctions",
                            "title": title,
                            "content": chunk_text,
                            "source_file": "WASALT_VERIFIED_DATA.md",
                            "source_url": rec_url
                        })
                else:
                    chunks.extend(self._split_record("wasalt", "auctions", "Wasalt Auctions", sec, "WASALT_VERIFIED_DATA.md", sec_url))

            elif "Verified Property Listings" in sec_header:
                lines = sec.split("\n")
                header_lines = []
                data_rows = []
                for line in lines:
                    if line.startswith("| Listing ID") or line.startswith("| :---"):
                        header_lines.append(line)
                    elif line.startswith("|") and not line.startswith("| Listing ID"):
                        data_rows.append(line)

                if data_rows and header_lines:
                    # Group listings by 4-5 rows per chunk to preserve complete records
                    step = 4
                    for idx in range(0, len(data_rows), step):
                        group = data_rows[idx:idx+step]
                        chunk_text = "## Wasalt Verified Property Listings\n**Source URLs**: https://wasalt.sa/en/properties-for-sale-in-riyadh | https://wasalt.sa/en/properties-for-rent-in-riyadh\n\n" + "\n".join(header_lines) + "\n" + "\n".join(group)
                        m_lid = re.search(r'\| (\d+) \| (Sale|Rent) \| (.*?) \| (.*?) \|', group[0])
                        title = f"Wasalt Property Listings ({m_lid.group(2) if m_lid else ''} {m_lid.group(3) if m_lid else ''} in Riyadh)"
                        rec_url = self._extract_url(group[0], "https://wasalt.sa/en/properties-for-sale-in-riyadh")
                        chunks.append({
                            "chunk_id": "",
                            "company": "wasalt",
                            "category": "listings",
                            "title": title,
                            "content": chunk_text,
                            "source_file": "WASALT_VERIFIED_DATA.md",
                            "source_url": rec_url
                        })
                else:
                    chunks.extend(self._split_record("wasalt", "listings", "Wasalt Property Listings", sec, "WASALT_VERIFIED_DATA.md", sec_url))

            elif "FAQs" in sec_header:
                sub_faqs = re.split(r'\n(?=### Q:)', sec)
                for sub in sub_faqs:
                    sub = sub.strip()
                    if not sub or sub.startswith("## "):
                        continue
                    m_q = re.match(r'### Q: (.*?)\n', sub)
                    q_title = m_q.group(1).strip() if m_q else "Wasalt FAQ"
                    chunks.append({
                        "chunk_id": "",
                        "company": "wasalt",
                        "category": "faqs",
                        "title": f"FAQ: {q_title}",
                        "content": f"## Official Wasalt FAQ\n**Source URL**: https://wasalt.sa/en\n\n{sub}",
                        "source_file": "WASALT_VERIFIED_DATA.md",
                        "source_url": "https://wasalt.sa/en"
                    })

            elif "Licensors" in sec_header:
                chunks.extend(self._split_record("wasalt", "licensing", "Government Licensors & Accreditations (REGA & Tourism)", sec, "WASALT_VERIFIED_DATA.md", sec_url))

            elif "Board" in sec_header or "Management" in sec_header:
                chunks.extend(self._split_record("wasalt", "governance", sec_header, sec, "WASALT_VERIFIED_DATA.md", sec_url))

            elif "Broker" in sec_header or "Wasalt Business" in sec_header:
                chunks.extend(self._split_record("wasalt", "broker_solutions", "Wasalt Business CRM & Broker Portal", sec, "WASALT_VERIFIED_DATA.md", sec_url))

            elif "Milestones" in sec_header:
                chunks.extend(self._split_record("wasalt", "milestones", "Historical Milestones & Growth Timeline", sec, "WASALT_VERIFIED_DATA.md", sec_url))

            elif "Taxonomy" in sec_header:
                chunks.extend(self._split_record("wasalt", "taxonomy", "Market Taxonomy & Geographic Coverage", sec, "WASALT_VERIFIED_DATA.md", sec_url))

            elif "Contact" in sec_header:
                chunks.extend(self._split_record("wasalt", "contact", "Corporate Contact & Customer Care", sec, "WASALT_VERIFIED_DATA.md", sec_url))

            else:
                chunks.extend(self._split_record("wasalt", "company_profile", sec_header, sec, "WASALT_VERIFIED_DATA.md", sec_url))

        for i, c in enumerate(chunks):
            c["chunk_id"] = f"ws_{c['category']}_{i+1:03d}"
        return chunks

    def _split_record(self, company: str, category: str, title: str, text: str, source_file: str, source_url: str) -> List[Dict[str, Any]]:
        text = text.strip()
        if len(text) <= self.target_chars:
            return [{
                "chunk_id": "",
                "company": company,
                "category": category,
                "title": title,
                "content": text,
                "source_file": source_file,
                "source_url": source_url
            }]

        chunks = []
        start = 0
        part = 1
        while start < len(text):
            end = min(start + self.target_chars, len(text))
            if end < len(text):
                # Try finding a natural paragraph or sentence boundary
                boundary = text.rfind("\n\n", start, end)
                if boundary == -1 or boundary < start + self.target_chars // 2:
                    boundary = text.rfind("\n", start, end)
                if boundary == -1 or boundary < start + self.target_chars // 2:
                    boundary = text.rfind(". ", start, end)
                if boundary != -1 and boundary > start:
                    end = boundary + (1 if text[boundary] == "." else 0)

            chunk_content = text[start:end].strip()
            if chunk_content:
                chunks.append({
                    "chunk_id": "",
                    "company": company,
                    "category": category,
                    "title": f"{title} (Part {part})",
                    "content": chunk_content,
                    "source_file": source_file,
                    "source_url": source_url
                })
                part += 1

            if end >= len(text):
                break
            start = max(end - self.overlap_chars, start + 1)

        return chunks
