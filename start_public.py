"""Start the customer portal through a temporary Cloudflare Quick Tunnel."""
import os
import queue
import re
import shutil
import socket
import subprocess
import sys
import threading
import time


START_PORT = int(os.environ.get("PORT", "8550"))
TUNNEL_URL_PATTERN = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com", re.IGNORECASE)


def _find_available_port(start_port):
    for port in range(start_port, start_port + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connection:
            if connection.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise RuntimeError(f"No available customer portal port found from {start_port} to {start_port + 19}.")


def _wait_for_local_server(process, port, timeout=30):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError("The customer portal exited before it became available.")
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.25)
    raise TimeoutError(f"The customer portal did not start on port {port} within {timeout}s.")


def _relay_tunnel_output(pipe, output_lines):
    for line in pipe:
        print(line, end="", file=sys.stderr, flush=True)
        output_lines.put(line)
    output_lines.put(None)


def _wait_for_tunnel_url(process, output_lines, timeout=60):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            line = output_lines.get(timeout=0.25)
        except queue.Empty:
            if process.poll() is not None:
                break
            continue
        if line is None:
            break
        match = TUNNEL_URL_PATTERN.search(line)
        if match:
            return match.group(0)
    raise RuntimeError(
        "Cloudflare did not provide a Quick Tunnel URL. Check the cloudflared output above."
    )


def _stop_process(process):
    if process is None or process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def main():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    cloudflared = shutil.which("cloudflared")
    if cloudflared is None:
        raise RuntimeError("cloudflared is required. Install it with: brew install cloudflared")
    port = _find_available_port(START_PORT)

    environment = os.environ.copy()
    environment["PORT"] = str(port)
    customer_server = None
    tunnel = None
    staff_app = None
    try:
        customer_server = subprocess.Popen(
            [sys.executable, os.path.join(project_dir, "customer_web.py")],
            cwd=project_dir,
            env=environment,
        )
        _wait_for_local_server(customer_server, port)

        tunnel_output = queue.Queue()
        tunnel = subprocess.Popen(
            [
                cloudflared,
                "tunnel",
                "--url",
                f"http://127.0.0.1:{port}",
                "--no-autoupdate",
            ],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        threading.Thread(
            target=_relay_tunnel_output,
            args=(tunnel.stdout, tunnel_output),
            daemon=True,
        ).start()
        public_url = _wait_for_tunnel_url(tunnel, tunnel_output)

        staff_environment = environment.copy()
        staff_environment["CUSTOMER_WEB_URL"] = public_url
        print(f"Customer portal local port: {port}", flush=True)
        print(f"Customer portal public URL: {public_url}", flush=True)
        print("Keep this window and this computer running while customers use the link.", flush=True)
        staff_app = subprocess.Popen(
            [sys.executable, os.path.join(project_dir, "ui_flet.py")],
            cwd=project_dir,
            env=staff_environment,
        )

        while staff_app.poll() is None:
            if customer_server.poll() is not None:
                raise RuntimeError("The customer portal stopped unexpectedly.")
            if tunnel.poll() is not None:
                raise RuntimeError("The Cloudflare tunnel stopped unexpectedly.")
            time.sleep(0.5)
        return staff_app.returncode
    finally:
        _stop_process(staff_app)
        _stop_process(tunnel)
        _stop_process(customer_server)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, TimeoutError) as error:
        print(f"Could not start the public app: {error}", file=sys.stderr)
        raise SystemExit(1) from error
