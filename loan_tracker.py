from datetime import datetime, date, timedelta
import re


def parse_due_date(due_date_str):
    """
    Parses various date formats gracefully (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, etc.).
    Returns a date object, or None if invalid/empty.
    """
    if not due_date_str:
        return None
    
    clean_str = str(due_date_str).strip()
    
    # Try standard date string formats
    formats = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%d %b %Y',
        '%d %B %Y'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(clean_str, fmt).date()
        except ValueError:
            continue
            
    # Try ISO/Regex extraction for YYYY-MM-DD
    match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', clean_str)
    if match:
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            pass

    return None


def calculate_loan_due_days(due_date_str, reference_date=None):
    """
    Calculates remaining days until the loan / EMI due date.
    
    Args:
        due_date_str (str): Stored loan due date (e.g. '2026-10-31').
        reference_date (date, optional): Reference date for calculation, defaults to today.
        
    Returns:
        dict: Complete dictionary containing days left, status, color tokens,
              stroke dash offsets for SVG countdown ring, and reminder messages.
    """
    if reference_date is None:
        reference_date = date.today()

    due_date = parse_due_date(due_date_str)
    circumference = 314.16  # 2 * pi * 50 for SVG r=50 circle

    if not due_date:
        return {
            'has_due_date': False,
            'raw_due_date': '',
            'formatted_due_date': 'Not Scheduled',
            'days_left': 0,
            'days_display': '--',
            'label_text': 'No Due Date',
            'is_overdue': False,
            'is_today': False,
            'status': 'no_loan',
            'status_color': '#94a3b8',
            'status_badge': 'No Schedule',
            'stroke_dashoffset': circumference,
            'reminder_message': 'No upcoming loan EMI scheduled. Set your due date anytime.'
        }

    delta_days = (due_date - reference_date).days
    formatted_due_date = due_date.strftime('%d %b %Y')

    if delta_days > 10:
        # Safe - More than 10 days left
        status = 'safe'
        status_color = '#16a34a'  # emerald green
        status_badge = 'On Track'
        label_text = 'Days Left'
        days_display = str(delta_days)
        is_overdue = False
        is_today = False
        
        # Calculate visual ring progress (based on 30-day EMI cycle)
        cycle_length = max(30, delta_days)
        fraction = min(1.0, max(0.0, delta_days / cycle_length))
        stroke_dashoffset = round(circumference * (1.0 - fraction), 2)
        reminder_message = f'EMI Reminder will be sent 15 days before due date ({formatted_due_date})'

    elif 4 <= delta_days <= 10:
        # Warning - Between 4 and 10 days left
        status = 'warning'
        status_color = '#eab308'  # amber yellow
        status_badge = 'Upcoming'
        label_text = 'Days Left'
        days_display = str(delta_days)
        is_overdue = False
        is_today = False
        
        fraction = delta_days / 30.0
        stroke_dashoffset = round(circumference * (1.0 - fraction), 2)
        reminder_message = f'Reminder: Upcoming EMI payment of {formatted_due_date} is due in {delta_days} days.'

    elif 1 <= delta_days <= 3:
        # Urgent - 1 to 3 days remaining
        status = 'urgent'
        status_color = '#f97316'  # orange
        status_badge = 'Action Required'
        label_text = 'Days Left'
        days_display = str(delta_days)
        is_overdue = False
        is_today = False
        
        fraction = delta_days / 30.0
        stroke_dashoffset = round(circumference * (1.0 - fraction), 2)
        reminder_message = f'Urgent Notice: Only {delta_days} day(s) left until EMI due date. Maintain sufficient balance!'

    elif delta_days == 0:
        # Due Today
        status = 'today'
        status_color = '#ef4444'  # red
        status_badge = 'Due Today'
        label_text = 'Due Today'
        days_display = '0'
        is_overdue = False
        is_today = True
        stroke_dashoffset = 0.0
        reminder_message = 'Attention: EMI payment is due today! Ensure bank account is funded.'

    else:
        # Overdue - delta_days < 0
        overdue_days = abs(delta_days)
        status = 'overdue'
        status_color = '#dc2626'  # deep red
        status_badge = 'Overdue'
        label_text = 'Days Overdue'
        days_display = str(overdue_days)
        is_overdue = True
        is_today = False
        stroke_dashoffset = 0.0
        reminder_message = f'Warning: Your EMI payment is overdue by {overdue_days} day(s). Contact your bank branch.'

    return {
        'has_due_date': True,
        'raw_due_date': due_date.strftime('%Y-%m-%d'),
        'formatted_due_date': formatted_due_date,
        'days_left': delta_days,
        'days_display': days_display,
        'label_text': label_text,
        'is_overdue': is_overdue,
        'is_today': is_today,
        'status': status,
        'status_color': status_color,
        'status_badge': status_badge,
        'stroke_dashoffset': stroke_dashoffset,
        'reminder_message': reminder_message
    }


def get_farmer_loan_tracker_summary(farmer, reference_date=None):
    """
    Helper function to prepare complete loan tracker data for the dashboard template.
    
    Args:
        farmer (dict or sqlite3.Row): The farmer database record.
        reference_date (date, optional): Reference date for testing.
        
    Returns:
        dict: Consolidated tracker data including farmer loan context.
    """
    if reference_date is None:
        reference_date = date.today()

    # Extract loan_due_date safely whether dict or sqlite3.Row
    due_date_str = None
    if isinstance(farmer, dict):
        due_date_str = farmer.get('loan_due_date')
    else:
        try:
            due_date_str = farmer['loan_due_date']
        except (IndexError, KeyError):
            due_date_str = None

    # If demo farmer Ramesh has no due date set yet, set a realistic 15-day due date
    if not due_date_str:
        farmer_name = farmer.get('full_name') if isinstance(farmer, dict) else farmer['full_name']
        if farmer_name == 'Ramesh Kumar':
            demo_due = reference_date + timedelta(days=15)
            due_date_str = demo_due.strftime('%Y-%m-%d')

    tracker_info = calculate_loan_due_days(due_date_str, reference_date=reference_date)

    # Attach loan amount and bank details for display
    loan_amt = farmer.get('loan_amount') if isinstance(farmer, dict) else farmer['loan_amount']
    bank = farmer.get('bank_name') if isinstance(farmer, dict) else farmer['bank_name']
    emi = farmer.get('existing_emi') if isinstance(farmer, dict) else farmer['existing_emi']

    tracker_info['loan_amount'] = loan_amt if (loan_amt and loan_amt.strip()) else '₹1,20,000'
    tracker_info['bank_name'] = bank if (bank and bank.strip()) else 'State Bank of India'
    tracker_info['existing_emi'] = emi if (emi and emi.strip()) else '₹8,500'

    return tracker_info


def update_farmer_loan_due_date(conn, farmer_id, new_due_date):
    """
    Updates the loan due date for a specific farmer in the database.
    
    Args:
        conn (sqlite3.Connection): Active database connection.
        farmer_id (int): Farmer ID.
        new_due_date (str): New due date string (YYYY-MM-DD).
        
    Returns:
        bool: True if successfully updated.
    """
    cursor = conn.cursor()
    cursor.execute('UPDATE farmers SET loan_due_date = ? WHERE id = ?', (new_due_date, farmer_id))
    conn.commit()
    return cursor.rowcount > 0
