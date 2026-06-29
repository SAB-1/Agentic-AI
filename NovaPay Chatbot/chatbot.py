from openai import OpenAI
from IPython.display import Markdown, display
from pypdf import PdfReader
import gradio as gr
from pydantic import BaseModel
from dotenv import load_dotenv
from container import file_search
import uuid
import os

load_dotenv(override=True)

os.environ["OPENAI_AGENTS_DISABLE_TRACING"]="1"
os.environ["OpenAI_API_KEY"]=os.getenv("API_TOKEN")
os.environ["OPENAI_BASE_URL"]="https://openrouter.ai/api/v1"


from agents import Agent, Runner, handoff, function_tool

pdfReader = PdfReader("Resources/NovaPay Profile.pdf")
prof_summary = ""
for page in pdfReader.pages:
    text = page.extract_text()
    if text:
        prof_summary += text + "\n"
    display(Markdown(text)) 


with open("Resources/Summary.txt", "r", encoding="utf-8") as file:
    summary = file.read() 


### Enquiry and General Questions

@function_tool
def search_documents(query: str) -> str:
    """ Search uploaded documents. """
    return f"Documents results for '{query}': ..."

@function_tool
def search_database(query: str) -> str:
    """ Search comapny database for customer info. """
    return f" Database results for '{query}': ..."


billing_agent = Agent(
    name="BillingSpecialist",
    instructions="""You handle billing questions:
    - Payment issues
    - Refunds
    - Invoice requests
    Be helpful and resolve issues quickly.""",
    tools=[search_documents]
)

technical_agent = Agent(
    name="TechnicalSupport",
    instructions="""You handle technical issues:
    - Bug reports
    - How-to questions
    - Feature requests
    Ask clarifying questions to understand the issue."""
)

General_agent=Agent(
    name="SupportSpecialist",
    instructions="""You are the first point of contact. Route customers immediately:
- Billing/payment/charge issues → transfer to BillingSpecialist RIGHT AWAY
- Technical problems → transfer to TechnicalSupport RIGHT AWAY

Do NOT ask clarifying questions if the intent is already clear. Transfer immediately.""",
    model="gpt-4o-mini",
    handoffs=(
        handoff(billing_agent),
        handoff(technical_agent),
    )
)



### NovaPay wallet

@function_tool
def airtime(phone_number: str, amount: int) -> str:
    return f"Paid ₦{amount} to {phone_number}"

Airtime_agent = Agent(
name = "AirtimeAgent",
instructions="You help users buy airtime. Always confirm amount and phone number before calling the tool. If the amount requested is not up to available balance, tell user INSUFFICIENT FUND ",
tools=[search_database, airtime]
) 

@function_tool
def data_purchase(phone_number: str, amount: int) -> str:
    return f"Paid ₦{amount} to {phone_number}"

Data_agent = Agent(
name = "DataAgent",
instructions="You help users buy data. Always confirm amount and phone number before calling the tool. If the amount requested is not up to available balance, tell user INSUFFICIENT FUND ",
tools=[search_database, data_purchase]
) 

@function_tool
def money_transfer_intra(account_number: int, amount: int, bank: str) -> str:
    return f"₦{amount} sent to {account_number}"

transactionIntra = Agent(
name = "MoneyTransferIntra",
instructions="You help users send money to other NovaPay wallet. Always confirm amount and account number before calling the tool, and the account number and name must match the receiving end." \
" If the amount requested is not up to available balance, tell user INSUFFICIENT FUND ",
tools=[search_database, money_transfer_intra]
) 

@function_tool
def money_transfer_external(account_number: int, amount: int, bank: str) -> str:
    return f"₦{amount + 10} sent to {account_number}"

transactionExternal = Agent(
name = "MoneyTransferExternal",
instructions="You help users send money to other banks with ₦10 charges for NovaPay. Always confirm amount and account number before calling the tool, and the account number and name must match the receiving end." \
" If the amount requested is not up to available balance, tell user INSUFFICIENT FUND ",
tools=[search_database, money_transfer_external]
) 

@function_tool
def bill_payment(bill_id: str, top_up_amount: int) -> str:
    return f"Paid ₦{top_up_amount + (top_up_amount*0.1)} to {bill_id}"

bill_agent = Agent(
name = "billpayment",
instructions="You help users top up their devices' services. Always confirm top_up_amount and bill_id before calling the tool. If the amount requested is not up to available balance, tell user INSUFFICIENT FUND ",
tools=[search_database, bill_payment]
) 


NovaWalletAgent=Agent(
    name="WalletAgentSpecialist",
    instructions="""You are responsible for wallet transactions. Your man responsiblities are  for instant transfers, bill payments, airtime, and data purchases.
Route customers immediately:
- For Airtime recharge → transfer to AirtimeAgent RIGHT AWAY
- For Data Subscription → transfer to DataAgent RIGHT AWAY
- For money transfer to NovaPay wallet(Intra-Bank) → transfer to MoneyTransferIntra RIGHT AWAY
- For money transfer to bank or wallet(Other Bank) → transfer to MoneyTransferExternal RIGHT AWAY
- For bill payment, such as DSTV recharge, GOTV recharge, Nepa bill payment WAEC & NECO Toekn buying → transfer to billpayment RIGHT AWAY

Do NOT ask clarifying questions if the intent is already clear. Transfer immediately.""",
    model="gpt-4o-mini",
    handoffs=(
        handoff(Airtime_agent),
        handoff(Data_agent),
        handoff(transactionIntra),
        handoff(transactionExternal),
        handoff(bill_agent)
    )
)


### NovaPay Business

@function_tool
def create_payment_link(amount: int, description: str, merchant_email: str) -> str:
    """Create a NovaPay payment link for a merchant. Always confirm before calling."""
    # TODO: Replace with real API call to NovaPay backend
    link_id = str(uuid.uuid4())[:8]
    return f"Payment link created: https://pay.novapay.ng/{link_id} for ₦{amount}. Desc: {description}"

payment_link_agent = Agent(
    name="PaymentLinkSpecialist",
    instructions="You handle NovaPay Payment Links. Use search_business_docs for fees/FAQ. Confirm amount+email before create_payment_link.",
    tools=[search_documents, create_payment_link]
)

@function_tool
def order_pos_terminal(merchant_name: str, address: str) -> str:
    """Order Android POS terminal. T+0 settlement."""
    return f"POS ordered for {merchant_name} to {address}. Ref: POS_{uuid.uuid4()[:6]}"

pos_agent = Agent(
    name="POSSpecialist",
    instructions="You handle NovaPay POS Terminals. T+0 settlement, Android devices. Use search_business_docs for specs.",
    tools=[search_documents, order_pos_terminal]
)


checkout_agent = Agent(
name="CheckoutSpecialist",
instructions="You handle NovaPay Online Checkout for WooCommerce/Shopify. Use search_business_docs for setup guides.",
tools=[search_documents]
)

business_triage = Agent(
    name="BusinessTriage",
    instructions="""You route NovaPay Business requests. Do NOT solve.
- Payment links, pay-by-link, fees -> PaymentLinkSpecialist
- POS, terminal, hardware -> POSSpecialist
- Online store, WooCommerce, Shopify, embed -> CheckoutSpecialist
Transfer immediately. No questions.""",
    model="gpt-4o-mini",
    handoffs=(
        handoff(payment_link_agent),
        handoff(pos_agent), 
        handoff(checkout_agent)
)
)

#
#@function_tool
#def merchant_payment(tool_type: str, merchant_id: str, amount: int) -> str:
 #   return f"Processed {tool_type} payment of ₦{amount + (amount * 0.14)} for merchant {merchant_id}"

#NovaPayBusinessAgent = Agent(
#    name="NovaPayBusinessAgent",
#    instructions="You help merchants accept payments via payment links, POS terminals, and online checkout. Always confirm merchant_id, tool_type (link, POS, checkout), and amount before calling the tool. If the amount requested is not up to available balance, tell user INSUFFICIENT FUND.",
#    tools=[search_database, merchant_payment]
#)


### NovaPay API

@function_tool
def generate_api_key(company_name: str, email: str) -> str:
    """Generate NovaPay API test keys for a developer. Always confirm first."""
    return f"Test keys generated for {company_name}. Email sent to {email}. Docs: docs.novapay.ng"

api_agent = Agent(
    name="APISpecialist",
    instructions=(
"You handle NovaPay API. NovaPay API lets businesses accept card and bank-transfer payments in apps/websites. "
"Use search_products_docs for endpoints, fees, docs. "
"To issue keys, confirm company_name + email, then call generate_api_key."
),
    tools=[search_documents, generate_api_key]
)


@function_tool
def api_payment(app_id: str, method: str, amount: int) -> str:
    return f"Processed {method} payment of ₦{amount} for app {app_id}"

NovaPayAPIAgent = Agent(
    name="NovaPayAPIAgent",
    instructions="You help developers accept card and bank-transfer payments inside their apps and websites. Always confirm app_id, method (card or bank-transfer), and amount before calling the tool. If the amount requested is not up to available balance, tell user INSUFFICIENT FUND.",
    tools=[search_database, api_payment]
)

api_triage = Agent(
name="APITriage",
instructions="""You help developers pay for API and also help them receive money on their website. Do NOT solve.
- API, developer, integration, keys, endpoints -> APISpecialist
- Receiving money on their webesite -> NovaPayAPIAgent
Transfer immediately. No questions.""",
model="gpt-4o-mini",
handoffs=(
    handoff(api_agent), 
    handoff(NovaPayAPIAgent)
)
)


### NovaPay Save:

@function_tool
def lock_funds(amount: int, duration_days: int, user_email: str) -> str:
    """Lock funds in NovaSave for a period to earn interest. Always confirm first."""
    plan_id = str(uuid.uuid4())[:8]
    return f"₦{amount} locked for {duration_days} days. Plan ID: NS_{plan_id}. Interest starts T+1."

novasave_agent = Agent(
name="NovaSaveSpecialist",
instructions=(
"You handle NovaSave. NovaSave lets users lock funds and earn interest over a chosen period. "
"Use search_products_docs for rates, min/max, early withdrawal policy. "
"To lock funds, confirm amount, duration, email, then call lock_funds."
),
tools=[search_documents, lock_funds]
)

save_triage = Agent(
name="SaveTriage",
instructions="""You route NovaPay product requests. Do NOT solve.
- API, developer, integration, keys, endpoints -> APISpecialist
- Savings, lock funds, interest, fixed plan -> NovaSaveSpecialist
Transfer immediately. No questions.""",
model="gpt-4o-mini",
handoffs=(
    handoff(novasave_agent)
)
)

### Triage Agent:

triage_agent = Agent(
name="MasterTriage",
instructions="""You are the first point of contact for NovaPay.
- Wallet: airtime, data, transfers, bills -> WalletTriage
- Business/Merchant: payment links, POS, checkout, onboarding -> BusinessTriage
- Saving: Locking up funds and earing interest -> SaveTriage
- API: Buying API and collecting money on website for API owners -> APISpecialist
- Billing/refunds/invoices -> BillingSpecialist
- Technical issues -> TechnicalSupport
Transfer immediately. No clarifying questions if intent is clear.""",
model="gpt-4o-mini",
handoffs=( 
handoff(NovaWalletAgent),
handoff(business_triage), 
handoff(api_triage),
handoff(save_triage),
handoff(billing_agent),
handoff(technical_agent),
)
)

result = await Runner.run(triage_agent, "I want to know how to fix my machine")
print(result.final_output)