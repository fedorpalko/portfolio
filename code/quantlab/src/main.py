# quantlab entry point
import os
import subprocess
import sys

def main():
    """
    Main entry point for the QuantLab application.
    Launches the Streamlit dashboard by default.
    """
    dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard.py')
    try:
        # Use the python executable from the virtual environment to run Streamlit
        python_executable = sys.executable 
        subprocess.run([python_executable, "-m", "streamlit", "run", dashboard_path], check=True)
    except FileNotFoundError:
        print("Error: 'streamlit' command not found or Python executable is incorrect.")
        print("Please make sure Streamlit is installed in your virtual environment and activated.")
        print("You can install it with: pip install streamlit")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        print(f"Error launching Streamlit dashboard: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()