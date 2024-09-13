# roles_proficiency_data.py

import pandas as pd

# Define the data with "Change Management" instead of "Time Management"
data = {
    'Role': [
        'Project Manager (PM)',
        'Business Analyst (BA)',
        'Developer / Software Engineer',
        'QA Analyst / Tester',
        'UX/UI Designer',
        'Systems Architect',
        'Data Analyst / Data Scientist',
        'DevOps Engineer',
        'Product Owner',
        'Subject Matter Expert (SME)',
        'Stakeholder',
        'Finance Manager'
    ],
    'Leadership': ['H', 'M', 'L', 'L', 'L', 'M', 'L', 'L', 'H', 'M', 'M', 'M'],
    'Technology': ['M', 'M', 'H', 'M', 'M', 'H', 'H', 'H', 'M', 'M', 'L', 'L'],
    'Data': ['M', 'H', 'M', 'M', 'M', 'H', 'H', 'M', 'M', 'M', 'L', 'H'],
    'Governance': ['H', 'M', 'L', 'L', 'L', 'M', 'M', 'M', 'H', 'M', 'H', 'H'],
    'Finance': ['H', 'M', 'L', 'L', 'L', 'L', 'M', 'L', 'H', 'M', 'H', 'H'],
    'Stakeholder Management': ['H', 'H', 'L', 'L', 'M', 'M', 'M', 'L', 'H', 'M', 'H', 'M'],
    'Communication': ['H', 'H', 'M', 'M', 'H', 'H', 'H', 'M', 'H', 'H', 'H', 'H'],
    'Risk Management': ['H', 'M', 'M', 'H', 'L', 'M', 'M', 'H', 'H', 'M', 'H', 'H'],
    'Compliance / Regulatory': ['M', 'M', 'L', 'M', 'L', 'M', 'M', 'M', 'M', 'M', 'M', 'H'],
    'Project Management': ['H', 'M', 'L', 'L', 'L', 'M', 'L', 'L', 'H', 'L', 'M', 'M'],
    'Domain Knowledge': ['M', 'H', 'M', 'M', 'M', 'H', 'H', 'M', 'H', 'H', 'H', 'M'],
    'Team Collaboration': ['H', 'H', 'H', 'H', 'H', 'H', 'M', 'H', 'H', 'H', 'M', 'M'],
    'Change Management': ['H', 'M', 'L', 'L', 'M', 'M', 'L', 'M', 'H', 'M', 'M', 'M']
}

# Create a DataFrame
df = pd.DataFrame(data)
