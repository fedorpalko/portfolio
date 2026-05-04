import socket
import json
import time
import sys

def send_signal(side, symbol="AAPL", qty=1):
    host = '127.0.0.1'
    port = 5555
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((host, port))
            message = json.dumps({
                "symbol": symbol,
                "side": side,
                "qty": qty,
                "type": "market"
            })
            s.sendall(message.encode())
            response = s.recv(1024)
            return response.decode()
    except ConnectionRefusedError:
        return "Error: C++ engine not running"

def countdown(seconds, action_msg):
    for i in range(seconds, 0, -1):
        sys.stdout.write(f"\r{action_msg} in {i} seconds...   ")
        sys.stdout.flush()
        time.sleep(1)
    print(f"\r{action_msg} NOW!          ")

def main():
    print("--- Livenode Integration Test: Open/Close Position ---")
    
    # Initial countdown
    countdown(5, "Opening AAPL position")
    
    # Open position
    print("Sending BUY signal...")
    resp = send_signal("buy")
    print(f"Engine Response: {resp}")
    
    if "success" not in resp.lower():
        print("Failed to open position. Aborting test.")
        return

    # Wait to close
    countdown(20, "Closing AAPL position")
    
    # Close position
    print("Sending SELL signal...")
    resp = send_signal("sell")
    print(f"Engine Response: {resp}")
    
    print("\nTest Complete.")

if __name__ == "__main__":
    main()
