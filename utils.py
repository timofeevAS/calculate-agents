import socket



def find_free_port(start_port, end_port):
    """
    Find a free port within the specified range.

    Parameters:
    - start_port (int): The start of the port range.
    - end_port (int): The end of the port range.

    Returns:
    - int: The first available port within the range, or None if no port is available.
    """
    for port in range(start_port, end_port + 1):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        if result != 0:
            return port

    return -1
