# NGO Data Scraper

## Overview
A Python script to scrape NGO details specifically from ngosindia.org's Rajasthan section. It collects NGO names, contact details, purposes, and websites, then saves the data into an Excel file for convenient access and analysis.

## Features
- Respects `robots.txt` rules to scrape ethically.
- Extracts NGO name, contact person, address, purpose/services, phone numbers, emails, and website.
- Scrapes the top 5 NGO profiles from Rajasthan listings.
- Saves data to an Excel file named `ngos_rajasthan_top5.xlsx`.
- Implements request delays to avoid overloading the server.

## Installation
Install required dependencies using:
