from __future__ import annotations
from jinja2 import Template

TEMPLATE = Template("""Subject: Public records request ({{ city_display }}): payments/contracts for {{ entity_name }}

Hello,

Pursuant to the Massachusetts Public Records Law, I am requesting copies of records sufficient to show:

1) All payments, reimbursements, disbursements, or other funds paid to {{ entity_name }} (including known aliases: {{ aliases }}) for the period {{ start_date }} through {{ end_date }}.
2) Any contracts, grants, purchase orders, or amendments associated with those payments, including contract numbers and award documents.
3) Any vendor registration records that identify the payee, including any vendor IDs or payee identifiers used in your systems.

If the entity appears under a parent organization or alternate vendor name, please include those records as well.

If any portion of this request is denied, please provide the specific legal basis for the denial and release all segregable portions.

Preferred format: electronic (CSV/Excel for payment ledgers; PDF for contract documents).

Thank you,
[Your Name]
""")

def build_request(city_display: str, entity_name: str, aliases: str, start_date: str, end_date: str) -> str:
    return TEMPLATE.render(
        city_display=city_display,
        entity_name=entity_name,
        aliases=aliases or "none known",
        start_date=start_date,
        end_date=end_date
    )
