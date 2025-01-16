"""Generate the log messages in a readme.
"""
from pathlib import Path
import yaml

output_dir = Path(Path(__file__).parent, 'output')

log_file = Path(*Path(__file__).parent.parts[:-2], 'src', 'valar_daemon', 'log_messages_source.yaml')
with log_file.open("r") as f:
    log_messages = yaml.safe_load(f)

# Stip trailing newline
for _, value in log_messages.items():
    value['description'] = value['description'].rstrip("\n")
    value['message'] = value['message'].rstrip("\n")

level_list = [10, 20, 30, 40, 50]
log_messages_sorted = dict(
    level10=[],
    level20=[],
    level30=[],
    level40=[],
    level50=[],
)

for message_name in log_messages:
    message_contents = log_messages[message_name]
    level = message_contents['level']
    log_messages_sorted[f'level{level}'].append(message_contents)

output = ''
output += '# Log messages'
output += '\n'
output += f'A total of {len(log_messages)} log messages below.'
output += '\n'
output += '## Level 10 (DEBUG)'
output += '\n'
for message in log_messages_sorted['level10']:
    # output += f"### {message['message']}"
    output += f"**{message['message']}**"
    output += '\n\n'
    output += f"Module: {message['module']}"
    output += '\n\n'
    output += f"Message: {message['description']}"
    output += '\n\n'
output += '## Level 20 (INFO)'
output += '\n'
for message in log_messages_sorted['level20']:
    output += f"**{message['message']}**"
    output += '\n\n'
    output += f"Module: {message['module']}"
    output += '\n\n'
    output += f"Message: {message['description']}"
    output += '\n\n'
output += '## Level 30 (WARNING)'
output += '\n'
for message in log_messages_sorted['level30']:
    output += f"**{message['message']}**"
    output += '\n\n'
    output += f"Module: {message['module']}"
    output += '\n\n'
    output += f"Message: {message['description']}"
    output += '\n\n'
output += '## Level 40 (ERROR)'
output += '\n'
for message in log_messages_sorted['level40']:
    output += f"**{message['message']}**"
    output += '\n\n'
    output += f"Module: {message['module']}"
    output += '\n\n'
    output += f"Message: {message['description']}"
    output += '\n\n'
output += '## Level 50 (CRITICAL)'
output += '\n'
for message in log_messages_sorted['level50']:
    output += f"**{message['message']}**"
    output += '\n\n'
    output += f"Module: {message['module']}"
    output += '\n\n'
    output += f"Message: {message['description']}"
    output += '\n\n'


out_file = Path(output_dir, 'logREADME.md')
with out_file.open("w") as f:
    f.write(output)
