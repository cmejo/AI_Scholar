
import json

with open('package.json', 'r') as f:
    package_json = json.load(f)

for script, command in package_json['scripts'].items():
    if 'python ' in command:
        package_json['scripts'][script] = command.replace('python ', 'python3 ')

with open('package.json', 'w') as f:
    json.dump(package_json, f, indent=2)
