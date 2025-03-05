import inspect
import json
import re
from typing import Any, Callable, Dict, List
from dataclasses import dataclass

def parse_docstring(docstring: str) -> tuple[str, dict[str, str]]:
    """
    Parses a docstring to extract the function description and parameter descriptions.
    Supports Numpy-style, Google-style, and Sphinx-style docstrings.
    
    Parameters
    ----------
    docstring : str
        The docstring to parse.
        
    Returns
    -------
    tuple[str, dict[str, str]]
    """
    if not docstring:
        raise ValueError("Docstring is required for function parsing.")
    
    lines = docstring.split("\n")
    description_lines = []
    param_descs = {}
    param_section = False
    current_param = None
    param_indent = None
    is_numpy_style = False
    
    for line in lines:
        
        if line.lower().startswith("parameters") or line.lower().startswith("args"):
            param_section = True
            continue
        
        if line.lower().startswith("return") or line.lower().startswith("raises") or line.lower().startswith("yields") or line.lower().startswith("returns"):
            break
        
        if param_section:
            if not line or line == "":
                    continue
            if current_param == None and param_indent == None:
                if line and line[0] == "-":
                    is_numpy_style = True
                    continue # Skip numpy-style parameter section header
                # Try to detect the indentation of the first parameter
                indent = len(line) - len(line.lstrip())
                if indent > 0:
                    param_indent = line[:indent]
                else:
                    param_indent = ""
            
            is_new_param_line = line.startswith(param_indent) if param_indent else len(line.lstrip()) == len(line)
            if is_new_param_line:
                if current_param:
                    param_descs[current_param[0]] = current_param[1].strip()
                    current_param = None
                line = line[len(param_indent):]
                param_name = line.split(" ")[0]
                param_name = param_name.rstrip(":")
                desc = ""
                if not is_numpy_style:
                    desc = line[len(param_name):].strip()
                    if desc:
                        # remove (type): from the description
                        desc = re.sub(r"\(.*?\):", "", desc).strip()
                        if desc[0] == "-" or desc[0] == ":":
                            desc = desc[1:].strip()
                current_param = (param_name, desc)
            elif current_param:
                current_param = (current_param[0], current_param[1] + "\n" + line.strip())
                
            
        else:
            description_lines.append(line)
    
    if current_param:
        param_descs[current_param[0]] = current_param[1].strip()
    description = " ".join(description_lines).strip()
    
    if not description:
        raise ValueError("Valid function description required.")
    
    return description, param_descs

def convert_functions_to_tools(functions: List[Callable]) -> List[Dict[str, Any]]:
    """
    Converts a list of functions to tools in OpenAI-like API format.
    
    Parameters
    ----------
    functions : list[Callable]
        The functions to convert.
        The functions must have type hints and a docstring in numpy, google, or sphinx style.
        
    Returns
    -------
    list[dict]
        The list of tools in OpenAI-like API format.
    """
    tools = []
    
    for func in functions:
        # Get function name
        func_name = func.__name__
        
        # Get docstring and parse it
        func_doc = inspect.getdoc(func) or ""
        description, param_descriptions = parse_docstring(func_doc)
        
        # Get type hints
        type_hints = inspect.signature(func).parameters
        n_params = len(type_hints)
        if len(param_descriptions.keys()) < n_params:
            raise ValueError(f"Number of parameter descriptions ({len(param_descriptions)}) does not match number of parameters ({n_params}).")
        
        # check names of parameters
        for param_name in type_hints.keys():
            if param_name not in param_descriptions:
                # try to match by using lower()
                param_name_lower = param_name.lower()
                fixed = False
                for key in param_descriptions.keys():
                    if key.lower() == param_name_lower:
                        param_descriptions[param_name] = param_descriptions.pop(key)
                        fixed = True
                        break
                if not fixed:
                    raise ValueError(f"Parameter description missing for parameter '{param_name}'.")
            p_description = param_descriptions[param_name]
            if not p_description or p_description == "":
                raise ValueError(f"Parameter description missing for parameter '{param_name}'.")
        # return_type = inspect.signature(func).return_annotation
        
        properties = {}
        required_params = []
        
        for param_name, param in type_hints.items():
            param_type = param.annotation if param.annotation is not inspect.Parameter.empty else None
            
            if param_type is None:
                raise ValueError(f"Type hint missing for parameter '{param_name}'.")
            
            # Convert Python types to JSON schema types
            type_mapping = {
                str: "string",
                int: "integer",
                float: "number",
                bool: "boolean",
                list: "array",
                dict: "object"
            }
            json_type = type_mapping.get(param_type, "string")
            
            properties[param_name] = {
                "type": json_type,
                "description": param_descriptions.get(param_name, f"{param_name} parameter")
            }
            required_params.append(param_name)
        
        tools.append({
            "type": "function",
            "function": {
                "name": func_name,
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required_params,
                    "additionalProperties": False
                },
                "strict": True
            }
        })
    
    return tools

@dataclass
class ToolParameter:
    """
    A parameter for a tool.
    
    Attributes
    ----------
    name : str
        The name of the parameter.
    type : str
        The type of the parameter.
    description : str
        The description of the parameter.
    """
    
    name: str
    type: str
    description: str

@dataclass
class ManualTool:
    """
    A manual tool for a toolbox.
    
    Attributes
    ----------
    name : str
        The name of the tool.
    function : Callable
        The function of the tool.
    description : str
        The description of the tool.
    parameters : List[ToolParameter]
        The parameters of the tool.
    """
    name: str
    function: Callable
    description: str
    parameters: List[ToolParameter]
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Converts the ManualTool instance into the expected tool format.
        
        Returns
        -------
        dict
            The tool as a dictionary.
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {param.name: {"type": param.type, "description": param.description} for param in self.parameters},
                    "required": [param.name for param in self.parameters],
                    "additionalProperties": False
                },
                "strict": True
            }
        }
        
@dataclass
class Toolbox:
    """
    A toolbox for storing and managing tools.
    
    Attributes
    ----------
    tools : dict[str, ManualTool | Callable]
        The tools in the toolbox.
    """
    
    tools: dict[str, ManualTool | Callable]
    
    def add_tool(self, tool: ManualTool | Callable):
        """
        Adds a tool to the toolbox.
        
        Parameters
        ----------
        tool : ManualTool | Callable
            The tool to add.
            If a callable function is provided, it needs to have type hints and a docstring in numpy, google, or sphinx style.
            
        """
        if isinstance(tool, ManualTool):
            self.tools[tool.name] = tool
        elif callable(tool):
            # check if the function can be converted to a tool
            _ = convert_functions_to_tools([tool])
            self.tools[tool.__name__] = tool
        else:
            raise ValueError("Invalid tool type. Must be a ManualTool or a callable function.")
        
    def remove_tool(self, tool_name: str):
        """
        Removes a tool from the toolbox.
        
        Parameters
        ----------
        tool_name : str
            The name of the tool to remove.
        """
        
        if tool_name in self.tools:
            del self.tools[tool_name]
        else:
            raise ValueError(f"Tool '{tool_name}' not found in toolbox.")
        
    def get_tool(self, tool_name: str) -> ManualTool | Callable:
        """
        Retrieves a tool from the toolbox.
        
        Parameters
        ----------
        tool_name : str
            The name of the tool to retrieve.
            
        Returns
        -------
        ManualTool | Callable
            The tool retrieved.
        """
        if tool_name in self.tools:
            return self.tools[tool_name]
        else:
            raise ValueError(f"Tool '{tool_name}' not found in toolbox.")
        
    def get_tools(self) -> list[dict]:
        """
        Converts the toolbox into a list of tools as dicts for OpenAI-like APIs.
        
        Returns
        -------
        list[dict]
            The list of tools as dicts.
        """
        
        tools = []
        for tool_name in self.tools.keys():
            if isinstance(self.tools[tool_name], ManualTool):
                tools.append(self.tools[tool_name].to_dict())
            else:
                tools.extend(convert_functions_to_tools([self.tools[tool_name]]))
                
        return tools
        
    def call_tool(self, tool_call: dict):
        """
        Calls a tool in the toolbox.
        
        OpenAI API returns a list of tool calls in the following format:
        
        {
            "id": "call_12345xyz",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": "{\"location\":\"Paris, France\"}"
            }
        }
        
        
        If the return value is not None, it will be converted to a string and
        returned to the API.
        For example, the function get_weather(location: str) should probably return a string like this:
        
        "The current temperature in Paris, France is 25°C."
        
        
        Parameters
        ----------
        tool_call : dict
            The tool call as received from an API.
            Must include the tool name and parameters.
            
        Returns
        -------
        Any
            The result of the tool call.
        """
        
        tool_function = None
        tool_name = tool_call.get("function", {}).get("name", None)
        if not tool_name:
            raise ValueError("Tool name not provided in tool call.")
        
        if tool_name in self.tools:
            tool = self.tools[tool_name]
            if isinstance(tool, ManualTool):
                tool_function = tool.function
            else:
                tool_function = tool
                
        if not tool_function:
            raise ValueError(f"Tool '{tool_name}' not found in toolbox.")
        
        tool_args = tool_call.get("function", {}).get("arguments", {})
        if not tool_args:
            raise ValueError("Tool arguments not provided in tool call.")
        
        try:
            args = json.loads(tool_args)
        except json.JSONDecodeError:
            raise ValueError("Invalid tool arguments provided.")
        
        return tool_function(**args)
        
        
        

if __name__ == "__main__":
    # Example function
    def get_weather(location: str) -> float:
        """
        Get current temperature for a given location.
        
        Parameters
        ----------
        location : str
            City and country e.g. Bogotá, Colombia
        """
        return 25.0  # Example return value
    
    def get_weather_google_docstring(location: str) -> float:
        """
        Get current temperature for a given location.
        
        Args:
            location (str): City and country e.g. Bogotá, Colombia
        """
        return 25.0

    # Convert function to tool format
    tools = convert_functions_to_tools([get_weather, get_weather_google_docstring])

    # Example of manually creating a tool
    tools.append(ManualTool(
        name="get_forecast",
        function=lambda city: f"Get weather forecast for {city}.",
        description="Get weather forecast for a given city.",
        parameters=[
            ToolParameter(name="city", type="string", description="City name"),
            ToolParameter(name="days", type="integer", description="Number of days for the forecast")
        ]
    ).to_dict())

    print(json.dumps(tools, indent=4))
