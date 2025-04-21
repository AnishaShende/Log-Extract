import re
import pandas as pd

# Set your paths
log_file = 'mxtrace.log'
excel_file = 'parsed_log_output.xlsx'

# Open and read file
with open(log_file, 'r') as file:
    content = file.read()

# Split into log entries
log_entries = content.split("**********")
parsed_data = []

# Regex patterns
header_pattern = re.compile(
    r"Error Trace::Version (?P<version>.*?)::(?P<datetime>[A-Za-z]{3} [A-Za-z]{3}\s+\d+ \d+:\d+:\d+ \d+)"
    r" \( (?P<time_detail>.*?) pid (?P<pid>\d+)\s+t@(?P<thread>[\-\d]+)(?: session (?P<session>[^ )]+))?"
)
message_pattern = re.compile(
    r"#\d+\s+(?P<level>\w+)\s+#(?P<code>\d+)\s+(?P<message>.+)"
)

# Parse each log chunk
for entry in log_entries:
    header_match = header_pattern.search(entry)
    message_match = message_pattern.search(entry)

    if header_match and message_match:
        data = {
            'Version': header_match.group('version'),
            'DateTime': header_match.group('datetime'),
            'TimeDetails': header_match.group('time_detail'),
            'PID': header_match.group('pid'),
            'Thread': header_match.group('thread'),
            'Session': header_match.group('session') if header_match.group('session') else '',
            'Level': message_match.group('level'),
            'Code': message_match.group('code'),
            'Message': message_match.group('message')
        }
        parsed_data.append(data)

# Convert to DataFrame
df = pd.DataFrame(parsed_data)

# Save to Excel
df.to_excel(excel_file, index=False)
print(f"✅ Parsed log data written to: {excel_file}")
