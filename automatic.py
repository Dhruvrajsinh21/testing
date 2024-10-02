import requests
import time
import random
import streamlit as st
from faker import Faker
import multiprocessing

# Initialize Faker
fake = Faker()

# Define the API URLs
signup_url = "http://3.108.52.92/api/auth/vendor/register/"
login_url = "http://3.108.52.92/vendorsignin/"
post_location_url = "http://3.108.52.92/vend_location/"
change_status_url = "http://3.108.52.92/vendor_status/"

# Function to generate a 10-digit phone number
def generate_10_digit_phone_number():
    return f"{fake.random_number(digits=10, fix_len=True)}"

# Function to register and perform all tasks for one vendor
def process_vendor():
    # Register user
    signup_payload = {
        "name": fake.name(),
        "email": fake.email(),
        "mobile_no": generate_10_digit_phone_number()
    }
    try:
        signup_response = requests.post(signup_url, json=signup_payload, timeout=10)
        if signup_response.status_code == 201:
            print(f"Signup successful: {signup_payload}")
        else:
            print(f"Signup failed: {signup_response.text}")
            return  # Skip this vendor if signup fails
    except requests.exceptions.RequestException as e:
        print(f"Error during signup: {e}")
        return

    # Login to get the bearer token
    login_payload = {"mobile_no": signup_payload["mobile_no"]}
    try:
        login_response = requests.post(login_url, json=login_payload, timeout=10)
        if login_response.status_code == 200:
            token = login_response.json().get("access")
            if token:
                print(f"Login successful. Token received for {signup_payload['mobile_no']}.")
            else:
                print(f"Token not found in the login response for {signup_payload['mobile_no']}.")
                return  # Skip this vendor if token is not found
        else:
            print(f"Login failed: {login_response.text}")
            return  # Skip this vendor if login fails
    except requests.exceptions.RequestException as e:
        print(f"Error during login: {e}")
        return

    # Post latitude and longitude
    location_payload = {"latitude": fake.latitude(), "longitude": fake.longitude()}
    headers = {"Authorization": f"Bearer {token}"}
    try:
        location_response = requests.post(post_location_url, json=location_payload, headers=headers, timeout=10)
        if location_response.status_code == 201:
            print(f"Location posted successfully for {signup_payload['mobile_no']}: {location_payload}")
        else:
            print(f"Failed to post location for {signup_payload['mobile_no']}: {location_response.text}")
            return  # Skip this vendor if location posting fails
    except requests.exceptions.RequestException as e:
        print(f"Error during location post: {e}")
        return

    # Change status to true
    status_payload = {"is_active": True}
    try:
        status_response = requests.post(change_status_url, json=status_payload, headers=headers, timeout=10)
        if status_response.status_code == 200:
            print(f"Status updated successfully for {signup_payload['mobile_no']}.")
        else:
            print(f"Failed to update status for {signup_payload['mobile_no']}: {status_response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Error during status update: {e}")

# Function to run the registration process continuously with random delays
def run_continuous_registration(stop_event):
    while not stop_event.is_set():  # Check if the stop event is set
        process_vendor()

        # Wait for a random amount of time between 1 to 2 hours before the next registration
        delay = random.uniform(3600, 7200)
        print(f"Waiting for {delay / 3600:.2f} hours before registering the next vendor...")
        stop_event.wait(delay)  # Wait for the specified delay or until the stop event is set

# Streamlit app logic
def main():
    st.title("Vendor Registration Simulator")

    if 'process' not in st.session_state:
        st.session_state['process'] = None

    # Start Button
    if st.button("Start"):
        if st.session_state['process'] is None:
            # Create an Event to signal stopping
            stop_event = multiprocessing.Event()
            st.session_state['process'] = multiprocessing.Process(target=run_continuous_registration, args=(stop_event,))
            st.session_state['stop_event'] = stop_event  # Store stop event in session state
            st.session_state['process'].start()
            st.write("Vendor registration started in the background.")

    # Stop Button
    if st.button("Stop"):
        if st.session_state['process'] is not None:
            st.session_state['stop_event'].set()  # Set the stop event to signal stopping
            st.session_state['process'].join()  # Wait for the process to finish
            st.session_state['process'] = None  # Reset the process in session state
            st.write("Vendor registration stopped.")

if __name__ == "__main__":
    main()
