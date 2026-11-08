# Calibration example 01: Smart Customs declaration assistant (written by the user)

The user wrote this as an example of a "good idea". The agent's output must reach the same **level of specificity**.

## Problem
People who order from Trendyol and other foreign sites struggle to file the declaration in the Smart Customs app.
- They cannot upload the invoice in the correct format.
- They choose the wrong category or sub-section, and the parcel gets stuck at customs.
- They convert TRY/USD to AZN incorrectly.
- Tracking numbers arrive late or do not show up in the system.
- They lose track of the $300 monthly duty-free limit and end up paying duty or storage fees.

## Solution (product)
A WhatsApp/Telegram bot or a Chrome Extension:
1. **Invoice OCR/AI:** the user sends a screenshot or PDF. The bot reads the product name, price, currency and tracking code.
2. **Ready declaration template:** the bot gives step-by-step values for each Smart Customs field, or the extension fills the fields with one click.
3. **$300 limit tracker:** the bot sums the month's declarations and warns the user before they cross the limit and pay duty.
4. **"Declare for me" service:** an operator or the bot files the full declaration for 1–2 AZN.

## Monetization
- **B2C:** a micro-payment of 0.50–1 AZN per declaration, or a monthly subscription of 3–5 AZN.
- **Small Instagram shops:** a monthly package for shops that resell Trendyol goods and handle many parcels.
- **B2B:** an API/SDK for cargo companies (Starex, Limak, Camex, etc.). Customs declaration questions are the most common support calls, so the integration claims to cut support load.

## What makes this example "good" (lessons for the agent)
1. **The problem is specific:** it names a platform (Trendyol), an app (Smart Customs) and a user group.
2. **The pain is split into sub-points:** each sub-point maps to a product feature.
3. **There is a mix of solutions:** a digital product (bot, extension), a service (operator) and B2B (API).
4. **The price is concrete:** amounts are in AZN.
5. **Customers and partners have names:** Starex, Limak, Camex.

## What the agent must add (the example lacks these)
- **Evidence links:** links to complaints and comments, plus how often they occur.
- **Fact checks:** the $300 limit, the 36% duty rate and the "70% less support load" claim must each be verified with a link. If a claim cannot be verified, the report marks it "doğrulanmadı" (not verified).
- **Competition:** do the cargo companies' own apps already solve this?
- **Market size estimate:** number of monthly parcels and number of paying users.
- **Risk:** Smart Customs is a state system. Automating it has legal and technical limits (ToS, captcha, API access).
