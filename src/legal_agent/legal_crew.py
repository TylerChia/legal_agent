from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai.agents.agent_builder.base_agent import BaseAgent
from typing import List
from dotenv import load_dotenv
from src.legal_agent.tools.web_search import WebSearchTool
from src.legal_agent.tools.send_email import SendEmailTool

load_dotenv()

@CrewBase
class LegalAgent():
    """LegalAgent Crew – an AI system that reviews, explains, and summarizes contracts for users."""
    agents: List[BaseAgent]
    tasks: List[Task]

    # === AGENTS ===
    @agent
    def researcher(self) -> Agent:
        """Extracts and classifies clauses from uploaded contracts."""
        return Agent(
            role="Contract Parsing Specialist",
            goal="Extract and classify clauses from uploaded contracts, identifying their purpose and context and detect any mentioned company or organization names "
            "for inclusion in downstream reporting.",
            backstory=(
                "You are an expert in understanding the structure of legal contracts. "
                "You can quickly identify sections like payment terms, confidentiality, termination, "
                "and liability, and rewrite them in structured, easy-to-parse text for further analysis."
            ),
            verbose=True,
            interactive=False
        )


    @agent
    def risk_analyzer(self) -> Agent:
        """Evaluates clauses for legal and ethical risks."""
        return Agent(
            role="Contract Risk Analyst",
            goal=(
                "Detect and rate potential legal and ethical risks in contract clauses. "
                "Identify terms that could cause legal harm or unfair obligations."
            ),
            backstory=(
                "You are a cautious and thorough legal analyst trained to spot red flags in agreements. "
                "You flag any terms that might be unfair, vague, one-sided, or harmful to the user’s rights."
            ),
            verbose=True,
            interactive=False
        )

    @agent
    def legal_researcher(self) -> Agent:
        """Finds and summarizes relevant legal info online."""
        return Agent(
            role="Legal Research Assistant",
            goal=(
                "Retrieve and summarize up-to-date, relevant legal information from the web "
                "to clarify complex terms or provide real-world examples."
            ),
            backstory=(
                "You are a skilled legal researcher capable of finding definitions, precedents, and explanations "
                "online using trusted sources and summarizing findings concisely."
            ),
            verbose=True,
            tools=[WebSearchTool()], 
            allow_delegation=False,
            interactive=False
        )


    @agent
    def user_advocate(self) -> Agent:
        """Explains the contract and risks in simple terms."""
        return Agent(
            role="Consumer Legal Advisor",
            goal="Summarize and simplify the contract analysis into clear, plain English explanations.",
            backstory=(
                "You are an empathetic communicator who translates legal findings into simple, actionable advice "
                "for non-lawyers. You never provide legal advice — only educational summaries."
            ),
            verbose=True,
            interactive=False
        )


    # @agent
    # def email_agent(self) -> Agent:
    #     return Agent(
    #         role="Email Delivery Specialist",
    #         goal=(
    #             "Your only responsibility is to send the final contract summary email using the SendEmailTool. "
    #             "You must call the tool to send the email yourself — do NOT describe it in text. "
    #             "Never output the final answer until the tool is executed successfully."
    #         ),
    #         backstory=(
    #             "You are responsible for securely delivering completed reports to users. "
    #             "You send the email yourself using the provided SendEmailTool. "
    #             "You always call the SendEmailTool directly — never skip this step."
    #             "Do NOT delegate this task to anyone else."
    #         ),
    #         verbose=True,
    #         tools=[SendEmailTool()],
    #         allow_delegation=False,  # 🚫 disable delegation
    #         max_iterations=3
    #     )


    # === TASKS ===
    @task
    def parse_contract(self) -> Task:
        """Extract clauses and structure the contract for analysis."""
        return Task(
            description=(
                "Analyze the following contract for the user {user_email}.\n\n"
                "Contract text:\n{contract_text}"
                "1. Identify and label key clauses like confidentiality, termination, payment, and liability.\n"
                "2. If a company name or organization name is present (e.g. 'This agreement is between X and Y'), "
                "extract the **main company name** and store it as `company_name` for later use. If no company name present, save company_name as '' (Empty string)\n"
                "3. Return a structured JSON containing `clauses`, `summaries`, and `company_name`."
            ),
            expected_output=(
                "A structured list of contract clauses with labels and short summaries for each section."
                "plus a 'company_name' field containing the main company mentioned."
            ),
            agent=self.researcher()
        )

    @task
    def analyze_risks(self) -> Task:
        """Evaluate the parsed contract clauses for potential risks."""
        return Task(
            description=(
                "Review the parsed clauses and assess each for potential risks, unfair terms, or ambiguity. "
                "If uncertain, request clarification from the Legal Researcher."
            ),
            expected_output=(
                "A risk report listing each clause, its risk level (Low/Medium/High), and explanations."
            ),
            agent=self.risk_analyzer()
        )

    @task
    def research_clarifications(self) -> Task:
        """Research unclear or complex clauses online."""
        return Task(
            description=(
                "Search the internet for definitions, precedents, or explanations about unclear terms. "
                "Summarize findings and cite at least one credible source."
            ),
            expected_output=(
                "A short paragraph summarizing findings with one or more source links."
            ),
            agent=self.legal_researcher()
        )


    @task
    def summarize_for_user(self) -> Task:
        """Write a user-friendly summary explaining key risks and terms."""
        return Task(
            description=(
                "Summarize the analysis for the user in plain English. Include risks, key terms, "
                "and disclaimers that this is not legal advice."
            ),
            expected_output=(
                "A markdown-formatted report containing:\n"
                "- A summary of the contract\n"
                "- A list of flagged clauses and risks\n"
                "- Any important dates or actions they should be aware of to avoid or take\n"
                "- Plain-English explanations\n"
                "- A disclaimer at the end"
            ),
            agent=self.user_advocate(),
            output_file="contract_summary.md"
        )

    # @task
    # def send_summary_email(self) -> Task:
    #     """Send the influencer contract summary to the creator."""
    #     return Task(
    #         description=(
    #             "Read the file 'contract_summary.md' and send its contents as an email using the SendEmailTool.\n"
    #             "Call the SendEmailTool directly with the following parameters:\n"
    #             "- recipient: {user_email}\n"
    #             "- subject: '{subject_line} company_name' (omit company_name if blank)\n"
    #             "- body: the full text content of 'contract_summary.md'\n\n"
    #             "- Important:\n"
    #             "- DO NOT output JSON.\n"
    #             "- DO NOT describe what you would do.\n"
    #             "You MUST ALWAYS execute the SendEmailTool — do NOT describe or simulate sending the email.\n"
    #             "- You must call the send_email() action directly.\n"
    #             "- Once you’ve executed the tool successfully, stop.\n"
    #             "Do NOT include extra metadata or explanations."
    #         ),
    #         expected_output=(
    #             "Successful email delivery confirmation from SendEmailTool."
    #         ),
    #         agent=self.email_agent(),
    #         context_variables=["company_name"],
    #         requires_execution=True
    #     )


    # @task
    # def send_summary_email(self) -> Task:
    #     """Email the final summary report to the user."""
    #     return Task(
    #         description=(
    #             "Using the SendEmailTool tool, read the contract summary from 'contract_summary.md' and send it to the user's email address: {user_email}."
    #             "Use the subject line format: '{subject_line} company_name' if company_name is available. Otherwise just use subject_line.\n"
    #             "Use the file content as the email body, include a short introduction, and end with a disclaimer that this is not legal advice. "
    #             "You must execute the SendEmailTool — do not summarize or explain what you would do. "
    #             "Once sent, consider the task complete — do NOT try to think further."
    #             "Output must be a JSON object with exactly these keys: "
    #             "`recipient` (string, email address), "
    #             "`subject` (string, subject line), "
    #             "`body` (string, the full contract summary). "
    #             "Do NOT include extra fields or metadata."
    #         ),
    #         expected_output=(
    #             'Example format:\n'
    #             '{\n'
    #             '  "recipient": "user@example.com",\n'
    #             '  "subject": "Contract Summary Report - 2025-11-03 - CompanyName",\n'
    #             '  "body": "Full contract summary here..."\n'
    #             '}'
    #         ),
    #         agent=self.email_agent(),
    #         context_variables=["company_name"],
    #         requires_execution=True
    #     )


    # === CREW ===
    @crew
    def crew(self) -> Crew:
        """Creates and configures the LegalAgent crew."""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            interactive=False,  # ← CRITICAL: Disable interactive prompts in production
            memory=False  # ← Optional: Disable memory to reduce complexity
        )
