import paramiko
import re
from flask import Flask, jsonify, send_file

app = Flask(__name__)

# Configure SSH details for the CAINE VM
SSH_HOST = '192.168.182.153'  # Replace with your VM's IP address
SSH_PORT = 22
SSH_USER = 'ksb'  # Replace with the username for the CAINE VM
SSH_PASSWORD = '12345'  # Use SSH password or key-based authentication

@app.route('/', methods=['GET'])
def Helloworld():
    return " Welcome to flask"


def execute_ssh_command(command):
    """Function to execute SSH commands on the VM."""
    try:
        # Create an SSH client
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically add unknown host keys
        
        # Connect to the VM using SSH
        client.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD)
        
        # Execute the command on the remote system (the VM)
        stdin, stdout, stderr = client.exec_command(command)
        
        # Read the output from stdout and stderr
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        # Close the SSH connection
        client.close()

        # Return the output or error
        if error:
            return error, 500
        return output, 200
    except Exception as e:
        return str(e), 500


def extract_file_path(tshark_output):
    """
    Extracts the file path from tshark output.
    Looks for lines containing "File: " and extracts the path.
    """
    match = re.search(r'File: "(.*?)"', tshark_output)
    if match:
        return match.group(1)
    return None



@app.route('/start_capture', methods=['GET'])
def start_capture():
    """Endpoint to start tshark and extract file path."""
    command = 'sudo tshark -i enp0s3 -c 10'  # Adjust the interface and capture settings
    output, status_code = execute_ssh_command(command)

    if status_code != 200:
        return jsonify({'error': output}), status_code

    # Extract file path from the tshark output
    file_path = extract_file_path(output)
    if not file_path:
        return jsonify({'error': 'Could not extract file path from tshark output.'}), 500

    # Return the file path to the client
    return jsonify({'file_path': file_path}), 200


@app.route('/show_capture_content', methods=['GET'])
def show_capture_content():
    """Endpoint to show the content of the capture file."""
    # This file path should ideally come from a client request or stored state
    capture_file_path = "/tmp/wireshark_enp0s388E3X2.pcapng"  # Replace with the parsed file path

    try:
        # Open and read the capture file content (assuming it's text-based; adjust for binary as needed)
        with open(capture_file_path, 'r') as f:
            file_content = f.read()

        return jsonify({'file_content': file_content}), 200
    except FileNotFoundError:
        return jsonify({'error': 'Capture file not found at the specified path.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download_capture_file', methods=['GET'])
def download_capture_file():
    """Endpoint to allow downloading of the capture file."""
    # This file path should ideally come from a client request or stored state
    capture_file_path = "/tmp/wireshark_enp0s388E3X2.pcapng"  # Replace with the parsed file path

    try:
        # Send the file as an attachment
        return send_file(capture_file_path, as_attachment=True)

    except FileNotFoundError:
        return jsonify({'error': 'Capture file not found at the specified path.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
