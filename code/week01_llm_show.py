import yaml
import os
from pydantic import SecretStr
from netmiko import ConnectHandler
from langchain_deepseek.chat_models import ChatDeepSeek
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda

# ================== Configuration Constants ==================
DEVICES_FILE_PATH = "../inventory/devices.yml"


# ================== Core Modules ==================

class DeviceManager:
    """Network device management class"""

    def __init__(self, devices_file_path: str):
        self.devices_file_path = devices_file_path
        self.devices = self._load_devices()

    def _load_devices(self) -> list:
        """Load device configuration file"""
        try:
            with open(self.devices_file_path, "r") as f:
                data = yaml.safe_load(f)
                return data.get("devices", [])
        except Exception as e:
            raise RuntimeError(f"Failed to load device configuration: {str(e)}")

    def find_device(self, identifier: str) -> dict:
        """Find device by IP or hostname"""
        for device in self.devices:
            if device["ip"] == identifier or device.get("hostname") == identifier:
                return device
        return {}


class LLMParser:
    """LLM parser class"""

    def __init__(self):
        self.api_key = self._get_api_key()
        self.llm = ChatDeepSeek(
            model="deepseek-chat",
            api_key=self.api_key
        )
        self.prompt = PromptTemplate(
            input_variables=["user_query"],
            template="""
You are a network assistant. Parse the user's query to extract:
    1. The commands to run on the network device (multiple commands separated by commas)
    2. The IP address of the network device, or the hostname of the network device
Ignore unnecessary words like 'run', 'execute', or 'please' if they are part of the command. If no valid commands are specified, return an empty command list.

Query: "{user_query}"

If the IP address of the network device is included in the query, then the Response Format is:
Commands: <command1>, <command2>, ...
IP: <device_ip>

If the hostname of the network device is included in the query, then the Response Format is:
Commands: <command1>, <command2>, ...
Hostname: <device_hostname>
"""
        )
        self.parse_chain = RunnableLambda(
            lambda inputs: self.llm.invoke(self.prompt.format(user_query=inputs["user_query"]))
        )

    def _get_api_key(self) -> SecretStr:
        """Get API key"""
        api_key = SecretStr(os.getenv("DEEPSEEK_API_KEY"))
        if not api_key:
            raise ValueError("Environment variable DEEPSEEK_API_KEY not set")
        return api_key

    def parse_query(self, user_query: str) -> dict:
        """Parse user query and return structured data"""
        print("Parsing user query...")
        response = self.parse_chain.invoke({"user_query": user_query})
        content = response.content

        result = {"commands": [], "identifier": None}

        for line in content.splitlines():
            if line.startswith("Commands:"):
                result["commands"] = [cmd.strip()
                                      for cmd in line.split("Commands:")[1].split(",")]
            elif line.startswith("IP:"):
                result["identifier"] = line.split("IP:")[1].strip()
            elif line.startswith("Hostname:"):
                result["identifier"] = line.split("Hostname:")[1].strip()

        # Clean and filter out empty commands
        cleaned_commands = [cmd.replace("run ", "")
                            .replace("execute ", "")
                            .strip() for cmd in result["commands"]]
        cleaned_commands = [cmd for cmd in cleaned_commands if cmd]  # Filter out empty strings

        result["commands"] = cleaned_commands
        return result


def execute_commands(device: dict, commands: list) -> str:
    """Execute commands on the device"""
    try:
        print(f"Connecting to {device['ip']}...")
        # Only include required parameters for ConnectHandler
        ssh_device = {
            "device_type": device["device_type"],
            "ip": device["ip"],
            "username": device["username"],
            "password": device["password"],
        }
        with ConnectHandler(**ssh_device) as ssh_conn:
            results = []
            for command in commands:
                print(f"Running command: {command}")
                output = ssh_conn.send_command(command)
                results.append(f"\n=== Output for '{command} on {device['ip']}' ===\n{output}")
            return "\n".join(results)
    except Exception as e:
        return f"Error: {str(e)}"



# ================== Main Program ==================
def main():
    """Main program entry point"""
    print("\n=== LLM-Powered Network Automation ===\n")

    device_manager = DeviceManager(DEVICES_FILE_PATH)
    llm_parser = LLMParser()

    while True:
        user_query = input("Enter your query (e.g., 'Run show version on 172.16.x.x') or type 'exit' to quit: ")
        user_query = user_query.strip()  # Remove leading/trailing whitespace

        if not user_query:
            continue  # Skip further processing and prompt again

        if user_query.lower() == 'exit':
            print("Exiting... Goodbye!")
            break

        try:
            # Parse query
            parsed_data = llm_parser.parse_query(user_query)

            # Validate command and identifier
            if not parsed_data["commands"]:
                print("No valid commands provided. Skipping execution.")
                continue

            # Find device
            device = device_manager.find_device(parsed_data["identifier"])
            if not device:
                print(f"Device {parsed_data['identifier']} does not exist")
                continue

            # Execute commands
            output = execute_commands(device, parsed_data["commands"])
            print("\n=== Command Output ===")
            print(f"{output}\n\n=================================================================\n")

        except Exception as e:
            print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()

