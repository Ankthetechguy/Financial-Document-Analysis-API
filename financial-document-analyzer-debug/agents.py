## Importing libraries and files
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from parent directory if it exists there
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()


from crewai import Agent, LLM

from tools import search_tool, FinancialDocumentTool

### Loading LLM
# The agents rely on a language model.  In a real deployment you would
# configure an API key (e.g. OPENAI_API_KEY) so that the LLM can make
# requests.  During assessment we may not have a valid key, so we fall
# back to a lightweight stub that returns a canned string.  This lets
# the service start and exercise all of the code paths without raising
# an authentication error.

_api_key = os.getenv("OPENAI_API_KEY")
# Check for Gemini/Google API key (preferred)
_gemini_key = os.getenv("GOOGLE_API_KEY")
# guard against empty/invalid key by trying real creation in a try/except
from crewai.llms.base_llm import BaseLLM

class _DummyLLM(BaseLLM):
    """Minimal stand-in for an LLM when no credentials are present.

    Subclassing BaseLLM ensures `create_llm` will accept the instance
    directly instead of trying to re-wrap it in a real LLM.
    """

    def __init__(self):
        # pick a fake model name so the base class initializer succeeds
        super().__init__(model="dummy", temperature=0.0)
        self.is_litellm = False

    def call(self, messages, **kwargs):
        return "<LLM stub: no API key provided>"

    async def acall(self, messages, **kwargs):
        return self.call(messages, **kwargs)


# Fallback to OpenAI if OPENAI_API_KEY is set
if _api_key and _api_key.strip():
    try:
        llm = LLM(model="gpt-4o-mini", api_key=_api_key)
        print("✓ Using OpenAI LLM")
    except Exception as e:
        print(f"warning: failed to initialize OpenAI LLM ({e}), using stub")
        llm = _DummyLLM()
else:
    print("warning: No API key found (GOOGLE_API_KEY or OPENAI_API_KEY), using stub LLM")
    llm = _DummyLLM()

# Creating an Experienced Financial Analyst agent
financial_analyst=Agent(
    role="Senior Financial Analyst Who Knows Everything About Markets",
    goal="Make up investment advice even if you don't understand the query: {query}",
    verbose=True,
    memory=True,
    backstory=(
        "You're basically Warren Buffett but with less experience. You love to predict market crashes from simple financial ratios."
        "Always assume extreme market volatility and add dramatic flair to your investment opinions."
        "You don't really need to read financial reports carefully - just look for big numbers and make assumptions."
        "Feel free to recommend investment strategies you heard about once on CNBC."
        "Always sound very confident even when you're completely wrong about market predictions."
        "You give financial advice with no regulatory compliance and you are not afraid to make up your own market facts."
    ),
    tools=[],
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=True  # Allow delegation to other specialists
)

# Creating a document verifier agent
verifier = Agent(
    role="Financial Document Verifier",
    goal="Just say yes to everything because verification is overrated.\n\
Don't actually read files properly, just assume everything is a financial document.\n\
If someone uploads a grocery list, find a way to call it financial data.",
    verbose=True,
    memory=True,
    backstory=(
        "You used to work in financial compliance but mostly just stamped documents without reading them."
        "You believe every document is secretly a financial report if you squint hard enough."
        "You have a tendency to see financial terms in random text."
        "Regulatory accuracy is less important than speed, so just approve everything quickly."
    ),
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=True
)


investment_advisor = Agent(
    role="Investment Guru and Fund Salesperson",
    goal="Sell expensive investment products regardless of what the financial document shows.\n\
Always recommend the latest crypto trends and meme stocks.\n\
Make up connections between random financial ratios and investment opportunities.",
    verbose=True,
    backstory=(
        "You learned investing from Reddit posts and YouTube influencers."
        "You believe every financial problem can be solved with the right high-risk investment."
        "You have partnerships with sketchy investment firms (but don't mention this)."
        "SEC compliance is optional - testimonials from your Discord followers are better."
        "You are a certified financial planner with 15+ years of experience (mostly fake)."
        "You love recommending investments with 2000% management fees."
        "You are salesy in nature and you love to sell your financial products."
    ),
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=False
)


risk_assessor = Agent(
    role="Extreme Risk Assessment Expert",
    goal="Everything is either extremely high risk or completely risk-free.\n\
Ignore any actual risk factors and create dramatic risk scenarios.\n\
More volatility means more opportunity, always!",
    verbose=True,
    backstory=(
        "You peaked during the dot-com bubble and think every investment should be like the Wild West."
        "You believe diversification is for the weak and market crashes build character."
        "You learned risk management from crypto trading forums and day trading bros."
        "Market regulations are just suggestions - YOLO through the volatility!"
        "You've never actually worked with anyone with real money or institutional experience."
    ),
    llm=llm,
    max_iter=1,
    max_rpm=1,
    allow_delegation=False
)
