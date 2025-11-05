from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv
from src.legal_agent.tools.web_search import WebSearchTool
from src.legal_agent.tools.send_email import SendEmailTool

load_dotenv()

## make more tailored to content creation and brand deal contracts
## more of a summary with what actions to take and what key dates submissions are due by
## what deliverables
## summary of each section
## legal concerns and exclusivity, white listing
## ownership of content ( can i post my own content )
## google calendar for deliverables
# fix buttons
# fix security

@CrewBase
class ContentCreatorLegalCrew():

    """LegalAgent Crew – an AI system that reviews, explains, and summarizes contracts for users."""
    agents: List[BaseAgent]
    tasks: List[Task]

    # === AGENTS ===
    @agent
    def researcher(self) -> Agent:
        """Extracts and classifies clauses from brand-deal / influencer contracts."""
        return Agent(
            role="Brand Deal Contract Parser",
            goal=(
                "Parse brand-deal contracts between company and social media creator. "
                "Do not make-up information that is not within the text. "
                "Identify deliverables, due dates, payment terms, ownership/licensing terms, exclusivity, "
                "royalties, usage rights, and any clauses that impose ongoing obligations or risks for the creator."
                "Extract and classify clauses from uploaded contracts, identifying their purpose and context and detect any mentioned company or organization names "
                "for inclusion in downstream reporting."
            ),
            backstory=(
                "You are an expert in influencer/brand agreements and content production contracts. "
                "You have knowledge of legal contracts and statements and can quickly identify concerns even if the legal jargon is complex. "
                "You know common language used for deliverables, timelines, approval flows, payment schedules, "
                "exclusivity, content ownership, licensing (perpetual/limited), attribution, moral clauses, "
                "and termination/kill fees. Produce structured outputs that downstream agents can consume."
            ),
            verbose=True
        )

    @agent
    def risk_analyzer(self) -> Agent:
        """Evaluates influencer-brand deal contracts for risks."""
        return Agent(
            role="Brand Deal Risk & Rights Analyst",
            goal=(
                "Identify and evaluate legal and business risks within influencer-brand contracts. "
                "Highlight clauses that could negatively impact the creator’s rights, revenue, or creative control."
                "Do not make-up information that is not within the text. "
            ),
            backstory=(
                "You are an experienced contract reviewer specializing in influencer marketing and brand partnerships. "
                "You understand common risks such as content ownership, exclusivity, perpetual usage rights, "
                "royalty clauses, and unfair deliverable obligations. You help creators protect their interests "
                "by identifying and explaining potential pitfalls clearly."
            ),
            verbose=True
        )

    @agent
    def legal_researcher(self) -> Agent:
        """Finds and summarizes relevant influencer marketing and contract info online."""
        return Agent(
            role="Influencer Contract Legal Researcher",
            goal=(
                "Retrieve and summarize up-to-date, relevant legal and business information about "
                "influencer-brand contracts, including usage rights, ownership, FTC disclosure laws, "
                "and fair compensation standards from the web to clarify complex terms or provide real-world examples from the input text."
                "Do not make-up information that is not within the text. "
            ),
            backstory=(
                "You are an expert legal researcher specializing in influencer marketing, digital rights, "
                "and brand deal compliance. You understand how brands and creators interact under modern law "
                "and can find relevant definitions, legal precedents, or best practices to clarify contract terms."
            ),
            verbose=True,
            tools=[WebSearchTool()],
            allow_delegation=False
        )


    @agent
    def user_advocate(self) -> Agent:
        """Summarizes influencer-brand contracts in clear, creator-friendly language."""
        return Agent(
            role="Influencer Contract Advisor",
            goal=(
                "Explain the influencer-brand contract in simple, creator-friendly language, "
                "highlighting what actions the creator needs to take, what rights they may be giving up, "
                "and any important due dates or red flags."
                "Do not make-up information that is not within the text. "
            ),
            backstory=(
                "You are an empathetic and knowledgeable contract explainer who helps social media creators "
                "understand their brand deals. You clearly outline deliverables, due dates, payment structure, "
                "and potential legal risks — like exclusivity, perpetual usage rights, or content ownership — "
                "in a way that’s informative but not legal advice."
            ),
            verbose=True
        )



    # === TASKS ===
    @task
    def parse_contract(self) -> Task:
        """Extract clauses, deliverables, dates, and legal concerns from a brand-deal contract."""
        return Task(
            description=(
                "Analyze the following brand-deal contract for the user {user_email}.\n\n"
                "Do NOT fabricate or infer information that is not explicitly stated in the contract text.\n"
                "If a section or detail is missing, leave it empty or omit it. Avoid assumptions.\n\n"
                "Contract text:\n{contract_text}\n\n"
                "Required actions:\n"
                "1) Identify and label key sections and clauses only if they are in the text, focusing on these categories:\n"
                "   - Deliverables (what the creator must produce; include format, platform, and quantity)\n"
                "   - Due dates and scheduling information for each deliverable\n"
                "   - Payment terms (amounts, schedule, invoicing, tax responsibilities)\n"
                "   - Ownership & Licensing\n"
                "   - Exclusivity / non-compete / whitelist requirements\n"
                "   - Royalties / rev-share / performance-based compensation\n"
                "   - Usage rights\n"
                "   - Approval process and timelines\n"
                "   - Termination and penalties\n"
                "   - Confidentiality / NDA\n"
                "   - Indemnity and liability\n"
                "   - Reporting, metrics, and acceptance criteria\n\n"
                "2) Extract and normalize all dates (ISO 8601 preferred) and associate them with deliverables or obligations.\n"
                "   Convert dates to PST (Pacific Standard Time)\n"
                "3) Extract the primary company/brand name mentioned and save it to 'company_name' if available.\n"
                "4) Produce a structured JSON output containing `deliverables`, `dates`, `legal_flags`, `clauses`, `company_name`, and `plain_english_summary`.\n\n"
                "Output must be valid JSON and contain ONLY the required fields — no commentary, no explanation, no example text.\n"
                "Dates need to have an associated deliverable.\n"
            ),
            expected_output=(
                "JSON object with the following keys (omit or leave empty if not applicable):\n"
                """{
                    "deliverables": [],
                    "dates": [],
                    "legal_flags": {},
                    "clauses": [],
                    "company_name": "",
                    "plain_english_summary": ""
                }"""
            ),
            agent=self.researcher(),
            context_variables=["company_name"]
        )


    @task
    def analyze_risks(self) -> Task:
        """Evaluate influencer-brand contract clauses for potential legal or business risks."""
        return Task(
            description=(
                "Examine the structured contract clauses produced by the previous step.\n\n"
                "Do not make-up information that is not within the contract text. "
                "For each clause, assess potential risks or concerns to the creator such as:\n"
                "- **Ownership & Usage Rights**: Does the brand gain perpetual or exclusive rights to the content?\n"
                "- **Exclusivity**: Does it prevent the creator from working with other brands in the same category?\n"
                "- **Approval & Revisions**: Are there unreasonable approval or reshoot terms?\n"
                "- **Royalties or Compensation**: Are payment terms vague or delayed?\n"
                "- **Termination or Liability**: Are there penalties or clauses unfairly favoring the brand?\n\n"
                "Rate each clause as Low, Medium, or High risk, and briefly explain why.\n"
                "Output a JSON report summarizing each clause with fields:\n"
                "- `clause_title`\n"
                "- `risk_level`\n"
                "- `risk_reason`\n"
                "- `recommendation` (optional advice to mitigate the issue)"
            ),
            expected_output=(
                "A JSON object containing a list of clauses with their associated `risk_level`, "
                "`risk_reason`, and optional `recommendation` for the creator."
            ),
            agent=self.risk_analyzer()
        )


    @task
    def research_clarifications(self) -> Task:
        """Research unclear or concerning influencer contract terms online."""
        return Task(
            description=(
                "Search the internet for definitions or real-world context for any unclear or risky terms "
                "in the influencer-brand contract, particularly related to:\n"
                "- Content ownership and usage rights (e.g., perpetual use, whitelisting)\n"
                "- Exclusivity and competition restrictions\n"
                "- Royalties, licensing, or revenue sharing\n"
                "- FTC disclosure and advertising compliance\n"
                "- Creator compensation norms and rights under influencer marketing law\n\n"
                "Summarize your findings clearly and cite at least one credible, recent source (e.g., FTC.gov, major law firm blogs, creator advocacy sites)."
            ),
            expected_output=(
                "A paragraph or short list summarizing findings with one or more cited, credible sources."
            ),
            agent=self.legal_researcher()
        )


    @task
    def summarize_for_user(self) -> Task:
        """Generate a creator-friendly summary explaining key deliverables, deadlines, and risks."""
        return Task(
            description=(
                "Using the parsed contract clauses and risk analysis, write a concise, friendly summary "
                "for the influencer who received this brand deal. Do not make-up information that is not within the contract text. Include if available:\n\n"
                "1. A short overview of the brand partnership and purpose of the contract.\n"
                "2. A list of **deliverables** (what the creator must produce: e.g. posts, videos, stories, etc.) "
                "with any associated **deadlines or posting dates**.\n"
                "3. A summary of **payment or compensation terms** (how and when they’ll be paid).\n"
                "4. Key **legal or business risks**, such as:\n"
                "   - Content ownership and rights (e.g., who owns the videos)\n"
                "   - Exclusivity or non-compete clauses\n"
                "   - Usage rights or whitelisting permissions\n"
                "   - Royalties, licensing, or perpetual usage terms\n"
                "   - FTC or disclosure requirements\n"
                "5. Actionable recommendations in plain English (e.g., “Double-check that payment terms are clear,” "
                "“Consider negotiating limited usage rights,” etc.).\n\n"
                "End the report with a clear disclaimer that this is not legal advice — "
                "it is an educational summary to help the creator understand their deal."
            ),
            expected_output=(
                "A markdown-formatted report with the following structure:\n"
                "## Brand Deal Summary\n"
                "## Deliverables & Deadlines\n"
                "## Payment Terms\n"
                "## Legal & Risk Concerns\n"
                "## Actionable Tips for the Creator\n"
                "### Disclaimer: This summary is for informational purposes only and not legal advice."
            ),
            agent=self.user_advocate(),
            output_file="contract_summary.md"
        )



    # === CREW ===
    @crew
    def crew(self) -> Crew:
        """Creates and configures the LegalAgent crew."""
        print("🔍 Available agents:", [agent.role for agent in self.agents])
        print("🔍 Available tasks:", [task.description[:50] + "..." for task in self.tasks])

        # Check for any references to email_agent
        for task in self.tasks:
            if hasattr(task, 'agent'):
                agent_role = getattr(task.agent, 'role', 'Unknown')
                print(f"🔍 Task '{task.description[:30]}...' assigned to agent: {agent_role}")
        """Creates and configures the LegalAgent crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True
        )
