import os
os.environ['CREWAI_TELEMETRY'] = 'false'

from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv
from src.legal_agent.tools.web_search import WebSearchTool
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
            verbose=True,
        )


    # @agent
    # def legal_researcher(self) -> Agent:
    #     """Finds and summarizes relevant influencer marketing and contract info online."""
    #     return Agent(
    #         role="Influencer Contract Legal Researcher",
    #         goal=(
    #             "Retrieve and summarize up-to-date, relevant legal and business information about "
    #             "influencer-brand contracts, including usage rights, ownership,"
    #             "and fair compensation standards from the web to clarify complex terms or provide real-world examples from the input text."
    #             "Do not make-up information that is not within the text. "
    #         ),
    #         backstory=(
    #             "You are an expert legal researcher specializing in influencer marketing, digital rights, "
    #             "and brand deal compliance. You understand how brands and creators interact under modern law "
    #             "and can find relevant definitions, legal precedents, or best practices to clarify contract terms."
    #         ),
    #         verbose=True,
    #         tools=[WebSearchTool()],
    #         allow_delegation=False,
    #     )

    # @agent
    # def legal_researcher(self) -> Agent:
    #     """Finds and summarizes relevant influencer marketing and contract info online."""
    #     return Agent(
    #         role="Influencer Contract Legal Researcher",
    #         goal=(
    #             "Quickly research unclear contract terms if needed."
    #         ),
    #         backstory=(
    #             "Fast legal researcher."
    #         ),
    #         verbose=True,
    #         tools=[WebSearchTool()],
    #         allow_delegation=False,
    #         max_iter=1
    #     )


    @agent
    def user_advocate(self) -> Agent:
        """Summarizes influencer-brand contracts in clear, creator-friendly language."""
        return Agent(
            role="Influencer Contract Advisor",
            goal=(
                "Explain the influencer-brand contract in simple, creator-friendly language, "
                "highlighting any important due dates or red flags."
                "Do not make-up information that is not within the text. "
            ),
            backstory=(
                "You are a knowledgeable contract explainer who helps social media creators "
                "understand their brand deals. You clearly outline deliverables, due dates, payment structure, "
                "and potential legal risks — like exclusivity, perpetual usage rights, or content ownership — "
                "in a way that’s informative but not legal advice."
            ),
            verbose=True
        )

    # @agent
    # def calendar_agent(self) -> Agent:
    #     """Adds contract deliverables and deadlines to Google Calendar."""
    #     return Agent(
    #         role="Contract Calendar Manager",
    #         goal=(
    #             "Extract deliverable dates from parsed contract data and create Google Calendar events "
    #             "with proper reminders. Only create events for deliverables that have clear due dates."
    #         ),
    #         backstory=(
    #             "You are an organized calendar management specialist who helps creators "
    #             "stay on top of their contract obligations by automatically adding "
    #             "deliverables and due dates to their Google Calendar. You carefully review "
    #             "parsed contract data to identify concrete deadlines and create professional "
    #             "calendar events with appropriate descriptions and reminders."
    #         ),
    #         verbose=True,
    #         tools=[SimpleGoogleCalendarTool()],
    #         allow_delegation=False,
    #         max_iter=1
    #     )



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
                "   - Due dates and scheduling information for each deliverable. Convert to Pacific Standard Time if necessary.\n"
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
                "- `risk_reason`"
            ),
            expected_output=(
                "A JSON object containing a list of clauses with their associated `risk_level`, "
                "`risk_reason`"
            ),
            agent=self.risk_analyzer()
        )


    # @task
    # def research_clarifications(self) -> Task:
    #     """Research unclear or concerning influencer contract terms online."""
    #     return Task(
    #         description=(
    #             "Search the internet for definitions or real-world context for any unclear or risky terms "
    #             "in the influencer-brand contract, particularly related to:\n"
    #             "- Content ownership and usage rights (e.g., perpetual use, whitelisting)\n"
    #             "- Exclusivity and competition restrictions\n"
    #             "- Royalties, licensing, or revenue sharing\n"
    #             "- Creator compensation norms and rights under influencer marketing law\n\n"
    #             "Summarize your findings clearly and cite at least one credible, recent source (e.g., FTC.gov, major law firm blogs, creator advocacy sites)."
    #         ),
    #         expected_output=(
    #             "A paragraph or short list summarizing findings with one or more cited, credible sources."
    #         ),
    #         agent=self.legal_researcher()
    #     )

    # @task
    # def research_clarifications(self) -> Task:
    #     """Research unclear or concerning influencer contract terms online."""
    #     return Task(
    #         description=(
    #             "ONLY research if contract has unclear perpetual rights or unusual clauses.\n"
    #             "Otherwise: 'No research needed'"
    #         ),
    #         expected_output=(
    #             "Brief research or 'No research needed'"
    #         ),
    #         agent=self.legal_researcher()
    #     )

    @task
    def extract_deliverables_for_calendar(self) -> Task:
        """Extract deliverables and due dates for calendar integration."""
        return Task(
            description=(
                "Extract ALL deliverables with due dates from the contract analysis.\n\n"
                "For each deliverable, provide:\n"
                "- summary: Brief title\n"
                "- description: What needs to be delivered\n" 
                "- start_date: Due date in YYYY-MM-DD format\n"
                "- start_time: Time in HH:MM format (24-hour) if specified, otherwise null\n"
                "- timezone: Timezone if specified (e.g., PST, EST, UTC), otherwise null\n"
                "- user_email: {user_email}\n\n"
                "Look for time indicators like:\n"
                "- 'by 5:00 PM PST'\n"
                "- 'due at 14:00 EST'  \n"
                "- 'submission deadline 9am PT'\n"
                "- 'before 3:00 PM Pacific Time'\n\n"
                "If no specific time is mentioned, set start_time to null for all-day events.\n"
                "Convert all times to 24-hour format (14:00 for 2:00 PM).\n"
                "Only include deliverables with explicit due dates."
            ),
            expected_output=(
                "JSON array of deliverables with 'summary', 'description', 'start_date', 'start_time, 'time_zone', 'user_email'"
            ),
            agent=self.researcher(),  # Use researcher since they already parse the contract
            context_variables=["user_email"],
            output_file="calendar_deliverables.json"
        )

    # @task
    # def add_deliverables_to_calendar(self) -> Task:
    #     """Extract deliverable dates and add them to Google Calendar."""
    #     return Task(
    #         description=(
    #             "Using the parsed contract information from previous tasks, identify all deliverables "
    #             "that have specific due dates and create Google Calendar events for each one.\n\n"
    #             "IMPORTANT: Call the calendar tool ONCE for each deliverable. Do not call it multiple times.\n"
    #             "If the tool says the event already exists, move to the next deliverable.\n\n"
    #             "Process:\n"
    #             "1. Review the parsed contract data for deliverables with clear due dates\n"
    #             "2. For each deliverable with a valid date:\n"
    #             "   - Create a calendar event with the deliverable title\n"
    #             "   - Include brief contract context and brief details in the event description\n"
    #             "   - Set the event date/time based on the due date\n"
    #             "   - Invite the user ({user_email}) to the event\n"
    #             "   - Call the calendar tool ONCE\n"
    #             "   - If it succeeds or says it exists, move on\n"
    #             "   - Do NOT retry or call multiple times\n\n"
    #             "3. Skip any deliverables without specific dates\n"
    #             "4. Provide a summary of events created\n\n"
    #             "Important: Only create events for deliverables that have explicit due dates "
    #             "mentioned in the contract. Do not assume or invent dates.\n\n"
    #             "Contract context available from previous analysis.\n"
    #             "Once the invitation is sent, DO NOT try to send again. Task is complete."

                
    #             "User: {user_email}"
    #         ),
    #         expected_output=(
    #             "A summary report of calendar events created including:\n"
    #             "- Number of events successfully created\n"
    #             "- List of deliverables with their dates\n"
    #             "- Any deliverables skipped due to missing dates\n"
    #             "- Confirmation that the user was invited to all events"
    #             "Include the phrase '✅ Calendar updates complete' at the end of your output."
    #         ),
    #         agent=self.calendar_agent(),
    #         context_variables=["user_email"]
    #     )

    @task
    def summarize_for_user(self) -> Task:
        """Generate a creator-friendly summary explaining key deliverables, deadlines, and risks."""
        return Task(
            description=(
                "Using the parsed contract clauses and risk analysis, write a concise, friendly summary "
                "for the influencer who received this brand deal. Do not make-up information that is not within the contract text. "
                "I would rather the output be more consise and summarized as succinctly as possible rather than being overly verbose. \n"
                "Include if available:\n\n"
                "1. A short overview of the brand partnership and purpose of the contract.\n"
                "2. A list of **deliverables** (what the creator must produce: e.g. posts, videos, stories, etc.) "
                "with any associated **deadlines or posting dates**.\n"
                "3. A summary of **payment or compensation terms** (how and when they’ll be paid).\n"
                "4. Key **legal or business risks**, such as:\n"
                "   - Content ownership and rights (e.g., who owns the videos)\n"
                "   - Exclusivity or non-compete clauses\n"
                "   - Usage rights or whitelisting permissions\n"
                "   - Royalties, licensing, or perpetual usage terms\n"
                "End the report with a clear disclaimer that this is not legal advice — "
                "it is an educational summary to help the creator understand their deal."
            ),
            expected_output=(
                "A markdown-formatted report with the following structure:\n"
                "## Brand Deal Summary\n"
                "## Deliverables & Deadlines\n"
                "## Payment Terms\n"
                "## Legal & Risk Concerns\n"
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
            verbose=True,
            memory=False,  # ← Optional: Disable memory to reduce complexity
            embedder=None  # Disable embedder
        )
