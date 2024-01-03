# D-Team Library Documentation

## Introduction

The D-Team library provides a Python interface for interacting with the D-Team platform. It includes features for connecting to accounts, fetching bulletins, retrieving family information, and sending notifications.  
All the code is provided 

## Installation

For now you can only copy-paste this code to your project. Pypi package will come soon.

## Usage

### Initializing the D-Team Object

```python
from d_team import DTeam

# Replace with your D-Team credentials
email = "your_email@example.com"
password = "your_password"

# Initialize D-Team object
d_team = DTeam(email, password)
```

### Connecting to the D-Team Account

```python
# Connect to the D-Team account
session = d_team.connexion(email, password)
```

### Fetching Bulletins

```python
# Fetch bulletins
bulletins_content = d_team.get_bulletins()
```

### Fetching Family Information

```python
# Fetch family information
families_info = d_team.fetch_familles()
```

### Fetching Upcoming Courses

```python
# Fetch upcoming courses
upcoming_courses = d_team.fetch_prochain_cours(jours = 1)
```

### Sending Email with Attachment

```python
# Send email with attachment
d_team.send_email_with_attachment(bulletins_content)
```

### Sending Telegram Notification

```python
# Send Telegram notification for upcoming courses
d_team.send_telegram_notification(upcoming_courses, families_info)
```

## License

This project is licensed under the CC BY-NC-SA 4.0 license - see the [LICENSE](https://creativecommons.org/licenses/by-nc-sa/4.0/) file for details.  
You can use the provided codes only for NonCommercial, giving credit to this repo and sharing your own york under the same license.  
You can contact me directly to get a specific license if needed ([mail](mailto:contact.applibot@gmail.com))
