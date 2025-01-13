#! /usr/bin/env python

'''
This script is used to run command lists. E.g.: power_on, input = hdmi2, volume=10, ambilight = ambilight_off
for this it calls the pylips lib with pythons subprocess functions

Additionally, it tries to make sure, that the desired state is achieved:
Example: TV on command comes in AND State of tv is already on  => the script does nothing
'''
import os
directory = os.path.abspath(os.path.dirname(__file__))

def get_json_result(output):
    print(f"parsing: {output}")
    lines = output.split(b"\n")

    filtered_json_output = []

    for l in lines:
        import json
        try:
            json_version = json.loads(l)
            filtered_json_output.append(json_version)
        except json.decoder.JSONDecodeError as ex:
            #this is expected if not a json object
            pass

    print(f"all json strings found: {filtered_json_output}")
    return filtered_json_output


def run_command(command: str):
    '''
    runs a pylips command
    we have to use subprocess here
    pylips yet processes the arguments if imported as a python module, which throws an error
    so therefore a direct import is not possible (yet)
    '''
    import subprocess
    script = os.path.join(directory, "pylips.py")
    print(f"running pylips with command: {command}")
    import sys
    #retrieve python: for virtual environments, execute pylips with the same interpreter
    python_executable = sys.executable
    result = subprocess.run([python_executable, script, "--command", command],
        capture_output=True)
    if result.returncode != 0:
        print(f"Warning: script --command {command} returned {result.returncode}")
    return result

def get_powerstate():
    '''
    returns the powerstate from the tvs response,
    filters out all unused ouptut, returns only the json object
    '''
    result = run_command("powerstate")
    all_results = get_json_result(result.stdout)

    currentstate = None
    if len(all_results) > 1:
        #script did several requests for some reason, we have to find the right one
        # take the first of them
        tmp = []
        for r in all_results:
            if "powerstate" in r:
                tmp.append(r)
        currentstate = tmp[0]
    elif len(all_results) == 0:
        print(f"Error: no json objects in script output: ")
        print(result.stdout)
        currentstate = {}
    else:
        currentstate = all_results[0]
    return currentstate

def phillips_on():
    currentstate = get_powerstate()

    if "powerstate" not in currentstate:
        print(f"Error: cannot retrieve powerstate, currentstate: {currentstate}")
        return

    if currentstate['powerstate'] == "On":
        print(f"tv is on, nothing to do")
    else:
        print(f"tv state is: {currentstate['powerstate']}, sending power key")
        power_on_result = run_command("standby")


def phillips_off():
    currentstate = get_powerstate()
    if currentstate['powerstate'] == "Off":
        print(f"tv is off, nothing to do")
    else:
        print(f"tv state is: {currentstate['powerstate']}, sending power key")
        power_on_result = run_command("standby")
        print(f"power_on: {power_on_result}")

def switch_to(input):
    '''
    switches to <input>
    prerequisites tv must be on
    '''
    result = run_command(input)
    json_response = get_json_result(result.stdout)
    resp = None
    if len(json_response) > 1:
        print(f"Warning: multiple json responses found, testing the last one")
        resp = json_response[len(json_response)]
    elif len(json_response) == 1:
        resp = json_response[0]
    else: 
        # len(json_response) == 0
        # this happens sometimes, my tv does the action, but no response
        # Maybe a timeout??
        print(f"Error: No Response object received")

    if "response" in resp:
        if resp["response"] == "OK":
            print(f"successfully switched to {input}")
        else:
            print(f"TV responded with: {resp}")
    else:
        print(f"Error: Switching to {input} returned an unexpected response: {resp}")


if __name__ == "__main__":
    
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--commandlist", nargs="+")
    args = parser.parse_args()

    for command in args.commandlist:
        if "power_on" == command:
            phillips_on()
        elif "power_off" == command:
            phillips_off()
        elif "powerstate" == command:
            state = get_powerstate()
            if 'powerstate' in state:
                print(f"tvs current state is: {state['powerstate']}")
            else:
                print(f"powerstate not retrievable: {state}")
        elif command.startswith("input"):
            switch_to(command)
        else:
            print(f"unknow command: {command}, skipping")