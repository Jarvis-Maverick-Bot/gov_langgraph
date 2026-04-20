@echo off
REM Start the NATS collaboration listener for Nova
REM Must be run from the Nexus project root (D:\Projects\Nexus)
REM Usage: listener_nova.bat

set PYTHONPATH=%CD%
python governance\collab\listener.py nova nats://192.168.31.64:4222
