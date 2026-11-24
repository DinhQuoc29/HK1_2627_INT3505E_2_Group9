"""Run Kaggle CLI over IPv4 without modifying system network settings."""
import socket
import sys
import urllib3.util.connection

urllib3.util.connection.allowed_gai_family = lambda: socket.AF_INET

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    from kaggle.cli import main
    main()
