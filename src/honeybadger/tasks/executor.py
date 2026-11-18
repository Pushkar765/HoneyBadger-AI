import logging
import subprocess

logger = logging.getLogger(__name__)

def execute_powershell(command: str, timeout: int = 30) -> str:
    """Executes a PowerShell command and returns the combined stdout and stderr.
    
    This is intended to be called only AFTER explicit user permission is granted.
    """
    logger.info("Executing user-approved PowerShell command: %s", command)
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        
        output = result.stdout.strip()
        err_output = result.stderr.strip()
        
        combined = []
        if output:
            combined.append(output)
        if err_output:
            combined.append(f"ERROR/WARNING:\n{err_output}")
            
        final_output = "\n".join(combined).strip()
        if not final_output:
            return "Command executed successfully with no output."
        return final_output
    except subprocess.TimeoutExpired:
        logger.error("Command execution timed out after %d seconds.", timeout)
        return f"Command timed out after {timeout} seconds."
    except Exception as exc:
        logger.error("Command execution failed: %s", exc)
        return f"Execution failed: {str(exc)}"
