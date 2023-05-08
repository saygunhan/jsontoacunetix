import json
import requests
import time

# Disable insecure warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Declare variables
MyAXURL = "https://acunetix_ip:3443/api/v1"
MyAPIKEY = "your_api_key"
FullScanProfileID = "11111111-1111-1111-1111-111111111111"
MyRequestHeaders = {'X-Auth': MyAPIKEY, 'Content-Type': 'application/json'}


def create_target(url, description):
    target_payload = {
        "address": url,
        "description": description
    }
    response = requests.post(MyAXURL + '/targets', json=target_payload, headers=MyRequestHeaders, verify=False)
    target_json = json.loads(response.content)
    target_id = target_json['target_id']
    return target_id


def trigger_scan(target_id, profile_id):
    scan_payload = {
        "profile_id": profile_id,
        "incremental": False,
        "schedule": {
            "disable": False,
            "start_date": None,
            "time_sensitive": False
        },
        "user_authorized_to_scan": "yes",
        "target_id": target_id
    }
    response = requests.post(MyAXURL + '/scans', json=scan_payload, headers=MyRequestHeaders, verify=False)
    scan_id = None

    if response.status_code == 201:
        if 'Location' in response.headers:
            location_header = response.headers['Location']
            scan_id = location_header.replace("/api/v1/scans/", "")
            print("Scan ID:", scan_id)
        else:
            print("Scan ID not found in response headers.")
    else:
        print("Failed to trigger scan. Response:", response.text)

    return scan_id


def get_active_scans():
    scan_status_response = requests.get(MyAXURL + '/scans', headers=MyRequestHeaders, verify=False)
    scan_status_json = scan_status_response.json()
    active_scans = 0

    if 'scans' in scan_status_json:
        for scan in scan_status_json['scans']:
                for mainkey in scan:
                    if mainkey == "current_session":
                        for subkey in scan[mainkey]:
                             if subkey == "status":
                                if scan[mainkey][subkey] == "processing" or scan[mainkey][subkey] == "queued" or scan[mainkey][subkey] == "scheduled":
                                    print("Scan ID:", scan['scan_id'], "is", scan[mainkey][subkey])
                                    active_scans += 1
                                    print("Active scans:", active_scans)
    return active_scans


def main():
    with open('output2.json') as json_file:
        data = json.load(json_file)
        targets = data['urls']
        company = data['company_name']

        active_scans = 0
        completed_scans = 0
        total_targets = len(targets)

        for target in targets:
            while active_scans >= 30:
                time.sleep(60)  # Wait for 1 minute
                active_scans = get_active_scans()
                print("Active scans:", active_scans, "Waiting for active scans to drop below 30...")

            target_id = create_target(target, company)
            if target_id is not None:
                scan_id = trigger_scan(target_id, FullScanProfileID)
                if scan_id is not None:
                    active_scans += 1
                    print("Scan started on target:", target)
                    print("Active scans:", active_scans)
                else:
                    print("Failed to trigger scan for target:", target_id)
                    print("Active scans:", active_scans)
            else:
                print("Failed to create target:", target)

        print("All targets loaded and scans triggered.")
        print("Active scans:", active_scans)
        print("Waiting for scans to complete...")

        while active_scans > 0:
            time.sleep(60)  # Wait for 1 minute
            active_scans = get_active_scans()
            print("Active scans:", active_scans)
            print("Scans completed:", completed_scans)
            print("Remaining targets:", total_targets - completed_scans - active_scans)

        print("All scans completed.")


if __name__ == "__main__":
    main()
