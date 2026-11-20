export type Company = "DarGlobal" | "Wasalt" | "Unified Search";
export type Source = {
  title: string;
  company: string;
  category: string;
  url: string;
  snippet?: string | undefined;
  score?: number | undefined;
};
export type ChatItem = {
  id: string;
  role: "user" | "assistant";
  parts: { type: "text"; text: string }[];
  sources?: Source[];
  model?: string;
  error?: boolean;
};
export type Thread = { id: string; title: string; company: Company; messages: ChatItem[] };
export const collections = [
  {
    company: "DarGlobal",
    description: "Extraordinary places. Exceptional partnerships.",
    categories: [
      "Company Profile",
      "Projects",
      "Board Members",
      "Brand Partnerships",
      "Press Releases",
    ],
    url: "https://darglobal.co.uk/",
  },
  {
    company: "Wasalt",
    description: "A connected perspective on Saudi real estate.",
    categories: [
      "Company Profile",
      "Services and Taxonomy",
      "FAQs",
      "Projects",
      "Auctions",
      "Property Listings",
    ],
    url: "https://wasalt.sa/",
  },
];
export const suggestions: Record<Company, { title: string; detail: string; question: string }[]> = {
  DarGlobal: [
    {
      title: "Meet DarGlobal",
      detail: "The vision behind the developments",
      question: "Tell me about DarGlobal.",
    },
    {
      title: "Discover the developments",
      detail: "Extraordinary homes around the world",
      question: "Explore its real estate developments.",
    },
    {
      title: "People behind the vision",
      detail: "Explore the board and leadership",
      question: "Who are the board members?",
    },
    {
      title: "Iconic brand partnerships",
      detail: "Where luxury and real estate meet",
      question: "What luxury brands does DarGlobal collaborate with?",
    },
  ],
  Wasalt: [
    {
      title: "Explore Wasalt services",
      detail: "A closer look at the platform",
      question: "What services does Wasalt offer?",
    },
    {
      title: "Licenses & credentials",
      detail: "Company and regulatory information",
      question: "What is Wasalt’s REGA license number?",
    },
    {
      title: "Find your property category",
      detail: "Explore the listing knowledge base",
      question: "What property categories are available in the knowledge base?",
    },
    {
      title: "Inside the auctions",
      detail: "Discover real estate opportunities",
      question: "Tell me about the auctions.",
    },
  ],
  "Unified Search": [
    {
      title: "Two brands, one perspective",
      detail: "Compare the available knowledge",
      question: "Compare the information available about DarGlobal and Wasalt.",
    },
    {
      title: "Explore a shared topic",
      detail: "Search across both collections",
      question: "Search both knowledge bases for real estate services.",
    },
  ],
};
export function demoAnswer(
  question: string,
  company: Company,
): { text: string; sources: Source[] } {
  const companies =
    company === "Unified Search" ? collections : collections.filter((c) => c.company === company);
  const sources = companies.map((c) => ({
    title: `${c.company} Company Profile`,
    company: c.company,
    category: "Company Information",
    url: c.url,
  }));
  const q = question.toLowerCase();
  if (q.includes("license") || q.includes("board"))
    return {
      text: `### ${q.includes("license") ? "Licenses & regulatory information" : "Board & leadership"}\n\nThis detail needs to be verified against the connected knowledge base. The frontend demonstration does not contain ${q.includes("license") ? "a verified REGA license number" : "a verified board member list"}, so I won’t invent one.\n\nThe official company homepage is included below as a **sample reference**, not evidence for a specific answer.`,
      sources,
    };
  if (company === "Unified Search")
    return {
      text: "### Two distinct real estate perspectives\n\nThis sample comparison illustrates how results from both collections can be presented together.\n\n| Collection | Knowledge focus |\n|---|---|\n| **DarGlobal** | Luxury developments, brand partnerships, leadership and company news |\n| **Wasalt** | Property listings, services, auctions and company information |\n\nThe connected backend will supply verified information and document-specific citations. **These are demonstration references only.**",
      sources,
    };
  if (company === "Wasalt")
    return {
      text: `### ${q.includes("auction") ? "Discover Wasalt auctions" : q.includes("categor") ? "Explore property information" : "Meet Wasalt"}\n\nWasalt’s sample collection brings together information about its real estate platform, property listings, services and auctions.\n\n**Available knowledge areas**\n- Company profile and platform information\n- Property listings and projects\n- Services, taxonomy and frequently asked questions\n- Auctions and related information\n\nThis is a **sample answer**. Current listings, auction dates, service terms and regulatory details must come from your connected backend.`,
      sources,
    };
  sources.push({
    title: q.includes("brand") ? "DarGlobal Brand Partnerships" : "DarGlobal Projects",
    company: "DarGlobal",
    category: q.includes("brand") ? "Brand Partnerships" : "Developments",
    url: "https://darglobal.co.uk/",
  });
  return {
    text: `### ${q.includes("brand") ? "Where iconic brands meet extraordinary homes" : q.includes("develop") ? "Explore DarGlobal developments" : "Meet DarGlobal"}\n\nDarGlobal’s sample collection offers a perspective on luxury real estate, distinctive developments and brand collaborations.\n\n**Explore the collection**\n- **Developments** — project information and residential concepts\n- **Brand partnerships** — collaborations across luxury and design\n- **Company & leadership** — company profile and board information\n- **News & press** — announcements and project updates\n\nThis is a **demonstration response**, not a live knowledge-base result. Your backend will provide verified project details and original document citations.`,
    sources,
  };
}
