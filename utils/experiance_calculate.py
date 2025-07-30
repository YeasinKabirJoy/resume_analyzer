from datetime import datetime

def calculate_total_experience(experiences):
    total_months = 0
    experiance = []
    for exp in experiences:
        start = datetime.strptime(exp["start"], "%b %Y")
        
        if exp["end"].lower() == "present":
            end = datetime.now()
        else:
            end = datetime.strptime(exp["end"], "%b %Y")

        # Add 1 to include the starting month
        months = (end.year - start.year) * 12 + (end.month - start.month) + 1
        experiance.append(round(months/12,2))
        total_months += months
    print(experiance)
    total_years = total_months / 12
    return round(total_years, 2),experiance

