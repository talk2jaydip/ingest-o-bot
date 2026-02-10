"""Debug specific link matching."""

# Simulate the link text after merging
link_text = "'Addressing Human Rights as Key to the COVID-19 Response'."
link_text_cleaned = link_text.strip('\'"''""')

# Simulate the page text
page_text = """. WHO has published guidance 'Addressing Human Rights as Key to the COVID-19
Response'. The guidance document highlights the importance of integrating a"""

print(f"Link text: [{link_text}]")
print(f"Cleaned: [{link_text_cleaned}]")
print(f"\nPage text:\n{page_text}\n")

# Test if it's in page_text
print(f"link_text_cleaned in page_text: {link_text_cleaned in page_text}")

# Try flexible whitespace
import re
flexible_pattern = re.escape(link_text_cleaned).replace(r'\ ', r'\s+')
print(f"\nFlexible pattern: {flexible_pattern}")
match = re.search(flexible_pattern, page_text, re.MULTILINE)
print(f"Flexible match: {match}")
if match:
    print(f"Matched text: [{match.group()}]")
